from django.db import models
from django.contrib.auth.models import User
# Create your models here.
#I am using the django's default User model for SignUp purpose


class Budget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - Budget: {self.amount}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]



    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=100) # Add category field.Need this for chart
    date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.description} - {self.amount} - {self.type} - {self.category}-{self.date}"

