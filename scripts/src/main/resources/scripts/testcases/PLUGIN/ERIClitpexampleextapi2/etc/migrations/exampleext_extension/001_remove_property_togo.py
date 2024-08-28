from litp.migration import BaseMigration
from litp.migration.operations import RemoveProperty, AddProperty

class Migration(BaseMigration):
    version = '1.0.2'
    operations = [
        RemoveProperty('example-item', 'togo', 'migVal'),
        AddProperty('example-item', 'newname', 'newMigVal'),
    ]
