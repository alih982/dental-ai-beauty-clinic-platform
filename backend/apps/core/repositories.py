"""
Base Repository Module - Generic Repository Pattern Implementation

Provides:
- Abstract repository interface
- Async database operations
- Specification pattern for complex queries
- Transaction management
"""
from typing import TypeVar, Generic, Optional, List, Dict, Any
from django.db import models, transaction
from django.db.models import QuerySet
from asgiref.sync import sync_to_async
import abc


T = TypeVar('T', bound=models.Model)


class Specification(abc.ABC):
    """
    Specification pattern for encapsulating query logic.
    Use to build complex, reusable query conditions.
    """
    
    @abc.abstractmethod
    def is_satisfied_by(self, obj: models.Model) -> bool:
        """Check if object satisfies the specification"""
        pass
    
    @abc.abstractmethod
    def to_queryset_filter(self) -> Dict[str, Any]:
        """Convert specification to Django QuerySet filter"""
        pass
    
    def __and__(self, other: 'Specification') -> 'AndSpecification':
        """Combine specifications with AND"""
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification') -> 'OrSpecification':
        """Combine specifications with OR"""
        return OrSpecification(self, other)


class AndSpecification(Specification):
    """AND combination of specifications"""
    
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2
    
    def is_satisfied_by(self, obj: models.Model) -> bool:
        return self.spec1.is_satisfied_by(obj) and self.spec2.is_satisfied_by(obj)
    
    def to_queryset_filter(self) -> Dict[str, Any]:
        # Merge filters (simplified, may need Q objects for complex cases)
        return {**self.spec1.to_queryset_filter(), **self.spec2.to_queryset_filter()}


class OrSpecification(Specification):
    """OR combination of specifications"""
    
    def __init__(self, spec1: Specification, spec2: Specification):
        self.spec1 = spec1
        self.spec2 = spec2
    
    def is_satisfied_by(self, obj: models.Model) -> bool:
        return self.spec1.is_satisfied_by(obj) or self.spec2.is_satisfied_by(obj)
    
    def to_queryset_filter(self) -> Dict[str, Any]:
        from django.db.models import Q
        # Would need to return Q objects for proper OR
        raise NotImplementedError("OR specifications require Q objects implementation")


class BaseRepository(Generic[T]):
    """
    Generic Repository Pattern for database operations.
    
    Benefits:
    - Decouples business logic from data access
    - Enables easy testing with mock repositories
    - Centralizes query logic
    - Supports async operations
    """
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    def get_queryset(self) -> QuerySet[T]:
        """Get base queryset - override for custom filtering"""
        return self.model_class.objects.all()
    
    # Sync CRUD Operations
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get object by ID"""
        try:
            return self.get_queryset().get(id=id)
        except self.model_class.DoesNotExist:
            return None
    
    def get_by(self, **filters) -> Optional[T]:
        """Get single object by filters"""
        try:
            return self.get_queryset().get(**filters)
        except self.model_class.DoesNotExist:
            return None
    
    def filter(self, **filters) -> QuerySet[T]:
        """Filter objects"""
        return self.get_queryset().filter(**filters)
    
    def all(self) -> QuerySet[T]:
        """Get all objects"""
        return self.get_queryset()
    
    def create(self, **data) -> T:
        """Create new object"""
        return self.model_class.objects.create(**data)
    
    def update(self, instance: T, **data) -> T:
        """Update existing object"""
        for key, value in data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def delete(self, instance: T) -> None:
        """Delete object (soft delete if supported)"""
        instance.delete()
    
    def count(self, **filters) -> int:
        """Count objects"""
        return self.filter(**filters).count()
    
    def exists(self, **filters) -> bool:
        """Check if object exists"""
        return self.filter(**filters).exists()
    
    def find_by_specification(self, spec: Specification) -> QuerySet[T]:
        """Find objects matching specification"""
        filters = spec.to_queryset_filter()
        return self.filter(**filters)
    
    # Async CRUD Operations (for high-performance API endpoints)
    
    async def aget_by_id(self, id: Any) -> Optional[T]:
        """Async get object by ID"""
        try:
            return await self.get_queryset().aget(id=id)
        except self.model_class.DoesNotExist:
            return None
    
    async def aget_by(self, **filters) -> Optional[T]:
        """Async get single object by filters"""
        try:
            return await self.get_queryset().aget(**filters)
        except self.model_class.DoesNotExist:
            return None
    
    async def afilter(self, **filters) -> List[T]:
        """Async filter objects"""
        queryset = self.get_queryset().filter(**filters)
        return await sync_to_async(list)(queryset)
    
    async def all_async(self) -> List[T]:
        """Async get all objects"""
        return await sync_to_async(list)(self.get_queryset())
    
    async def acreate(self, **data) -> T:
        """Async create new object"""
        return await self.model_class.objects.acreate(**data)
    
    async def aupdate(self, instance: T, **data) -> T:
        """Async update existing object"""
        for key, value in data.items():
            setattr(instance, key, value)
        await sync_to_async(instance.save)()
        return instance
    
    async def adelete(self, instance: T) -> None:
        """Async delete object"""
        await sync_to_async(instance.delete)()
    
    async def acount(self, **filters) -> int:
        """Async count objects"""
        queryset = self.get_queryset().filter(**filters)
        return await queryset.acount()
    
    async def aexists(self, **filters) -> bool:
        """Async check if object exists"""
        queryset = self.get_queryset().filter(**filters)
        return await queryset.aexists()
    
    # Batch Operations
    
    async def abulk_create(self, instances: List[T]) -> List[T]:
        """Async bulk create multiple objects"""
        return await self.model_class.objects.abulk_create(instances)
    
    def bulk_create(self, instances: List[T]) -> List[T]:
        """Bulk create multiple objects"""
        return self.model_class.objects.bulk_create(instances)
    
    # Transaction Support
    
    @staticmethod
    @transaction.atomic
    def with_transaction(func):
        """Decorator for running function in transaction"""
        return func
    
    async def in_transaction_async(self, func, *args, **kwargs):
        """Run async function in transaction"""
        async with transaction.atomic():
            return await func(*args, **kwargs)


class ReadOnlyRepository(BaseRepository[T]):
    """
    Read-only repository for query-heavy services.
    Prevents accidental data modifications.
    """
    
    def create(self, **data) -> T:
        raise NotImplementedError("Cannot create in read-only repository")
    
    def update(self, instance: T, **data) -> T:
        raise NotImplementedError("Cannot update in read-only repository")
    
    def delete(self, instance: T) -> None:
        raise NotImplementedError("Cannot delete in read-only repository")
    
    async def acreate(self, **data) -> T:
        raise NotImplementedError("Cannot create in read-only repository")
    
    async def aupdate(self, instance: T, **data) -> T:
        raise NotImplementedError("Cannot update in read-only repository")
    
    async def adelete(self, instance: T) -> None:
        raise NotImplementedError("Cannot delete in read-only repository")
