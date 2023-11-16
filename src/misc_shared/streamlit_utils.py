from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from logging import Logger
from random import choices
from string import ascii_lowercase
from typing import ClassVar, Generic, Optional, Type, TypeVar

import streamlit as st
from humanize import precisedelta
from pydantic import BaseModel, ConfigDict, Field
from simplesingletable import DynamoDbMemory, DynamoDbResource, DynamoDbVersionedResource
from simplesingletable.models import ResourceConfig

T = TypeVar("T", bound=BaseModel)


def date_id(now=None):
    now = now or datetime.utcnow()
    return now.strftime("%Y%m%d%H%M%S") + "".join(choices(ascii_lowercase, k=6))


class StreamlitSessionBase(BaseModel):
    session_id: str = Field(default_factory=date_id)
    expires_at: Optional[Decimal] = None

    @property
    def expires_in(self) -> str:
        if self.expires_at:
            now = datetime.utcnow()
            expiration = datetime.fromtimestamp(float(self.expires_at))

            time_remaining = expiration - now
            if time_remaining.total_seconds() < 0:
                return f"expired {precisedelta(time_remaining)} ago"
            else:
                return f"expires in {precisedelta(time_remaining)}"

        else:
            return ""

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        self.save_to_session_state()

    def save_to_session_state(self):
        datakey = self.__class__.__name__
        if datakey not in st.session_state:
            st.session_state[datakey] = {}
        for k, v in self.model_dump().items():
            st.session_state[datakey][k] = v

    # model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")


SessionType = TypeVar("SessionType", bound=StreamlitSessionBase)


@dataclass
class SessionManagerInterface(ABC, Generic[SessionType]):
    logger: Logger

    @abstractmethod
    def persist_session(self, session: SessionType):
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionType]:
        pass

    @abstractmethod
    def get_session_model(self) -> Type[SessionType]:
        pass

    @abstractmethod
    def get_query_param_name(self) -> str:
        pass

    def set_session_expiration(self, session: SessionType, expiration: datetime | timedelta):
        match expiration:
            case datetime():
                expires_at = expiration.timestamp()
            case timedelta():
                expires_at = (datetime.utcnow() + expiration).timestamp()
            case _:
                raise ValueError("Invalid type for expiration")
        expires_at = Decimal(str(expires_at).split(".")[0])
        session.expires_at = expires_at
        self.persist_session(session)
        return session

    def init_session(self, expiration: Optional[datetime | timedelta] = None) -> SessionType:
        datakey = self.get_session_model().__name__
        query_session = st.experimental_get_query_params().get(self.get_query_param_name())
        if query_session:
            query_session = query_session[0]

            if st.session_state.get(datakey, {}).get("session_id") != query_session:
                # no, the requested session isn't loaded -- clear out any existing session data
                self.logger.info("Clearing outdated session")
                self.clear_session_data()

        if datakey not in st.session_state:
            st.session_state[datakey] = {}

        session: Optional[T] = None
        if st.session_state[datakey].get("session_id"):
            # since we have a session id in the session_state already, we've done an init and can load the data
            session = self.get_session_model().model_validate(st.session_state[datakey])
        elif query_session:
            self.logger.info("Loading session from query param")
            session = self.get_session(query_session)
            if not session:
                self.logger.warning("No session matching query param found")
                existing_params = st.experimental_get_query_params()
                existing_params.pop(self.get_query_param_name())
                st.experimental_set_query_params(**existing_params)

        if not session:
            self.logger.info(f"Starting new session {datakey=}")
            if expiration:
                match expiration:
                    case datetime():
                        expires_at = expiration.timestamp()
                    case timedelta():
                        expires_at = (datetime.utcnow() + expiration).timestamp()
                    case _:
                        raise ValueError("Invalid type for expiration")
                session = self.get_session_model()(expires_at=expires_at)
            else:
                session = self.get_session_model()()

        session.save_to_session_state()
        return session

    def clear_session_data(self):
        datakey = self.get_session_model().__name__
        st.session_state.pop(datakey, None)

    def switch_session(self, switch_to_session_id):
        incoming_session = self.get_session(switch_to_session_id)
        self.clear_session_data()
        incoming_session.save_to_session_state()


class MemorySessionManager(SessionManagerInterface[SessionType]):
    def __init__(
        self,
        model_type: Type[SessionType],
        memory: DynamoDbMemory,
        logger,
        ttl_attribute_name: Optional[str] = None,
        query_param_name: Optional[str] = None,
        enable_versioning: bool = False,
    ):
        if query_param_name is None:
            query_param_name = model_type.__name__

        self._query_param_name = query_param_name
        self.logger = logger
        self.enable_versioning = enable_versioning
        self._memory = memory
        self.ttl_attribute_name = ttl_attribute_name

        if not issubclass(model_type, StreamlitSessionBase):
            raise TypeError("model_type must be a subclass of StreamlitSessionBase")
        self.model_type = model_type

        if enable_versioning:

            class DbSession(DynamoDbVersionedResource):
                session: model_type
                model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

                def to_dynamodb_item(self, v0_object: bool = False) -> dict:
                    base = super().to_dynamodb_item(v0_object)
                    if self.session.expires_at and v0_object and ttl_attribute_name:
                        base[ttl_attribute_name] = self.session.expires_at
                    return base

        else:

            class DbSession(DynamoDbResource):
                session: model_type
                model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
                resource_config = ResourceConfig(compress_data=True)

                def to_dynamodb_item(self) -> dict:
                    base = super().to_dynamodb_item()
                    if self.session.expires_at and ttl_attribute_name:
                        base[ttl_attribute_name] = self.session.expires_at
                    return base

        self._db_model = DbSession

    def get_session_model(self) -> Type[SessionType]:
        return self.model_type

    def get_query_param_name(self) -> str:
        return self._query_param_name

    def persist_session(self, session: SessionType):
        existing = self.get_db_session(session.session_id)
        if not existing:
            self._memory.create_new(self._db_model, data={"session": session}, override_id=session.session_id)
        else:
            if existing.session != session:
                self._memory.update_existing(existing, update_obj={"session": session})
        existing_params = st.experimental_get_query_params()
        existing_params[self.get_query_param_name()] = session.session_id
        st.experimental_set_query_params(**existing_params)

    def get_session(self, session_id: str) -> Optional[SessionType]:
        self.logger.info("Getting session from database")
        if db_session := self.get_db_session(session_id):
            return db_session.session

    # not part of the interface
    def get_db_session(self, session_id: str):
        return self._memory.get_existing(session_id, data_class=self._db_model)
