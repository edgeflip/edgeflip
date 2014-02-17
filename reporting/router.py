class RedshiftRouter(object):
    def db_for_read(self, model, instance=None):
        if model._meta.app_label == 'reporting':
            return 'redshift'
        return 'default'

    def db_for_write(self, model, instance=None):
        if model._meta.app_label == 'reporting':
            return 'redshift'
        return 'default'

    def allow_syncdb(self, db, model):
        if db == "redshift":
            return model._meta.app_label == 'reporting'
        elif model._meta.app_label == 'reporting':
            return False
        return None
