"""
Database Router for Read Replicas
Separates read and write operations for scalability
"""


class ReadReplicaRouter:
    """
    Route database operations to read replicas for SELECT queries.
    All writes go to the primary database.
    
    Setup:
        1. Configure read replica in settings.py
        2. Add router to DATABASE_ROUTERS setting
    """
    
    def db_for_read(self, model, **hints):
        """
        Reads go to read replica.
        """
        return 'read_replica'
    
    def db_for_write(self, model, **hints):
        """
        Writes go to primary database.
        """
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database.
        """
        db_set = {'default', 'read_replica'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on the default database.
        """
        return db == 'default'


class ExplicitDatabaseRouter:
    """
    Route specific apps to specific databases.
    Useful for microservices architecture or database sharding.
    """
    
    # Define app to database mapping
    APP_DB_MAPPING = {
        'appointments': 'default',
        'doctors': 'default',
        'patients': 'default',
        # Add more mappings as needed
    }
    
    def db_for_read(self, model, **hints):
        """Route reads based on app label"""
        if model._meta.app_label in self.APP_DB_MAPPING:
            return self.APP_DB_MAPPING[model._meta.app_label]
        return None
    
    def db_for_write(self, model, **hints):
        """Route writes based on app label"""
        if model._meta.app_label in self.APP_DB_MAPPING:
            return self.APP_DB_MAPPING[model._meta.app_label]
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both are in the same database"""
        db1 = self.APP_DB_MAPPING.get(obj1._meta.app_label)
        db2 = self.APP_DB_MAPPING.get(obj2._meta.app_label)
        if db1 and db2:
            return db1 == db2
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Allow migrations only for apps in the database"""
        if app_label in self.APP_DB_MAPPING:
            return self.APP_DB_MAPPING[app_label] == db
        return None
