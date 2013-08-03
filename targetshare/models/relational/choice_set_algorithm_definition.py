from django.db import models


class ChoiceSetAlgorithmDefinition(models.Model):

    choice_set_algorithm_definition_id = models.AutoField(
        db_column='choice_set_algoritm_definition_id',
        primary_key=True
    )
    choice_set_algorithm = models.ForeignKey(
        'ChoiceSetAlgorithm',
        db_column='choice_set_algoritm_id'
    )
    algorithm_definition = models.TextField(null=True)
    start_dt = models.DateTimeField(auto_now_add=True)
    end_dt = models.DateTimeField(null=True)

    class Meta:
        db_table = 'choice_set_algoritm_definitions'
