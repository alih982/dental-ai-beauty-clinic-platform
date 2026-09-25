"""
Base Service Module - Service Layer Pattern Implementation

Provides:
- Business logic encapsulation
- Transaction management
- Event publishing for inter-service communication
- Validation and error handling
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
import abc
import logging

from .repositories import BaseRepository


T = TypeVar('T')
logger = logging.getLogger(__name__)


class DomainEvent:
    """
    Domain Event for event-driven architecture.
    Services publish events when important actions occur.
    """
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
    
    def __repr__(self):
        return f"<DomainEvent: {self.event_type}>"


class EventPublisher:
    """
    Simple event publisher for inter-service communication.
    In production, replace with message broker (RabbitMQ, Kafka, etc.)
    """
    
    _handlers: Dict[str, List[callable]] = {}
    
    @classmethod
    def subscribe(cls, event_type: str, handler: callable):
        """Subscribe handler to event type"""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
        logger.info(f"Subscribed handler to {event_type}")
    
    @classmethod
    async def publish(cls, event: DomainEvent):
        """Publish event to all subscribers"""
        handlers = cls._handlers.get(event.event_type, [])
        logger.info(f"Publishing event: {event.event_type} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)
    
    @classmethod
    def publish_sync(cls, event: DomainEvent):
        """Synchronous event publishing"""
        handlers = cls._handlers.get(event.event_type, [])
        logger.info(f"Publishing event (sync): {event.event_type}")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)


class BaseService(Generic[T]):
    """
    Base service class for business logic.
    
    Responsibilities:
    - Coordinate between repositories
    - Implement business rules and validations
    - Manage transactions
    - Publish domain events
    
    Guidelines:
    - Keep views thin, put logic here
    - One service per aggregate root
    - Services can call other services
    - Never access database directly, use repositories
    """
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data before processing.
        Override in subclass for custom validation.
        Raise ValidationError if invalid.
        """
        return data
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID with logging"""
        self.logger.debug(f"Getting {self.repository.model_class.__name__} by id: {id}")
        return self.repository.get_by_id(id)
    
    async def aget_by_id(self, id: Any) -> Optional[T]:
        """Async get entity by ID"""
        self.logger.debug(f"Getting {self.repository.model_class.__name__} by id: {id} (async)")
        return await self.repository.aget_by_id(id)
    
    def list_all(self, **filters) -> List[T]:
        """List all entities with optional filters"""
        self.logger.debug(f"Listing {self.repository.model_class.__name__} with filters: {filters}")
        queryset = self.repository.filter(**filters) if filters else self.repository.all()
        return list(queryset)
    
    async def alist_all(self, **filters) -> List[T]:
        """Async list all entities"""
        self.logger.debug(f"Listing {self.repository.model_class.__name__} with filters: {filters} (async)")
        return await self.repository.afilter(**filters) if filters else await self.repository.all_async()
    
    @transaction.atomic
    def create(self, data: Dict[str, Any], publish_event: bool = True) -> T:
        """
        Create new entity with validation and event publishing.
        Runs in transaction.
        """
        self.logger.info(f"Creating {self.repository.model_class.__name__}")
        
        # Validate data
        validated_data = self.validate(data)
        
        # Create entity
        entity = self.repository.create(**validated_data)
        
        # Publish domain event
        if publish_event:
            event = DomainEvent(
                event_type=f"{self.repository.model_class.__name__}.created",
                data={"id": entity.id, "entity": entity}
            )
            EventPublisher.publish_sync(event)
        
        self.logger.info(f"Created {self.repository.model_class.__name__}: {entity.id}")
        return entity
    
    async def acreate(self, data: Dict[str, Any], publish_event: bool = True) -> T:
        """Async create with validation and event publishing"""
        self.logger.info(f"Creating {self.repository.model_class.__name__} (async)")
        
        # Validate data
        validated_data = self.validate(data)
        
        # Create entity
        async with transaction.atomic():
            entity = await self.repository.acreate(**validated_data)
            
            # Publish domain event
            if publish_event:
                event = DomainEvent(
                    event_type=f"{self.repository.model_class.__name__}.created",
                    data={"id": entity.id, "entity": entity}
                )
                await EventPublisher.publish(event)
        
        self.logger.info(f"Created {self.repository.model_class.__name__}: {entity.id}")
        return entity
    
    @transaction.atomic
    def update(self, id: Any, data: Dict[str, Any], publish_event: bool = True) -> Optional[T]:
        """Update entity with validation and event publishing"""
        self.logger.info(f"Updating {self.repository.model_class.__name__}: {id}")
        
        # Get existing entity
        entity = self.repository.get_by_id(id)
        if not entity:
            self.logger.warning(f"{self.repository.model_class.__name__} not found: {id}")
            return None
        
        # Validate data
        validated_data = self.validate(data)
        
        # Update entity
        updated_entity = self.repository.update(entity, **validated_data)
        
        # Publish event
        if publish_event:
            event = DomainEvent(
                event_type=f"{self.repository.model_class.__name__}.updated",
                data={"id": updated_entity.id, "entity": updated_entity, "changes": data}
            )
            EventPublisher.publish_sync(event)
        
        self.logger.info(f"Updated {self.repository.model_class.__name__}: {id}")
        return updated_entity
    
    async def aupdate(self, id: Any, data: Dict[str, Any], publish_event: bool = True) -> Optional[T]:
        """Async update with validation and event publishing"""
        self.logger.info(f"Updating {self.repository.model_class.__name__}: {id} (async)")
        
        # Get existing entity
        entity = await self.repository.aget_by_id(id)
        if not entity:
            self.logger.warning(f"{self.repository.model_class.__name__} not found: {id}")
            return None
        
        # Validate data
        validated_data = self.validate(data)
        
        # Update entity in transaction
        async with transaction.atomic():
            updated_entity = await self.repository.aupdate(entity, **validated_data)
            
            # Publish event
            if publish_event:
                event = DomainEvent(
                    event_type=f"{self.repository.model_class.__name__}.updated",
                    data={"id": updated_entity.id, "entity": updated_entity, "changes": data}
                )
                await EventPublisher.publish(event)
        
        self.logger.info(f"Updated {self.repository.model_class.__name__}: {id}")
        return updated_entity
    
    @transaction.atomic
    def delete(self, id: Any, publish_event: bool = True) -> bool:
        """Delete entity with event publishing"""
        self.logger.info(f"Deleting {self.repository.model_class.__name__}: {id}")
        
        entity = self.repository.get_by_id(id)
        if not entity:
            self.logger.warning(f"{self.repository.model_class.__name__} not found: {id}")
            return False
        
        self.repository.delete(entity)
        
        # Publish event
        if publish_event:
            event = DomainEvent(
                event_type=f"{self.repository.model_class.__name__}.deleted",
                data={"id": id}
            )
            EventPublisher.publish_sync(event)
        
        self.logger.info(f"Deleted {self.repository.model_class.__name__}: {id}")
        return True
    
    async def adelete(self, id: Any, publish_event: bool = True) -> bool:
        """Async delete with event publishing"""
        self.logger.info(f"Deleting {self.repository.model_class.__name__}: {id} (async)")
        
        entity = await self.repository.aget_by_id(id)
        if not entity:
            self.logger.warning(f"{self.repository.model_class.__name__} not found: {id}")
            return False
        
        async with transaction.atomic():
            await self.repository.adelete(entity)
            
            # Publish event
            if publish_event:
                event = DomainEvent(
                    event_type=f"{self.repository.model_class.__name__}.deleted",
                    data={"id": id}
                )
                await EventPublisher.publish(event)
        
        self.logger.info(f"Deleted {self.repository.model_class.__name__}: {id}")
        return True


# Import asyncio for async event handling
import asyncio
