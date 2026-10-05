from django.db.models.signals import post_save
from django.dispatch import receiver

from transactions.models import Transaction

from .services import sync_employee_from_salary_transaction


@receiver(post_save, sender=Transaction)
def update_employee_on_salary_payment(sender, instance: Transaction, **kwargs):
    sync_employee_from_salary_transaction(instance)
