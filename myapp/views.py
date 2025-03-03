from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout#greate
from django.contrib.auth.models import User
from .models import Budget, Transaction
from .forms import BudgetForm, TransactionForm
from django.shortcuts import get_object_or_404, redirect
import json
from decimal import Decimal
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os
import google.generativeai as genai
import re
from django.contrib.sessions.models import Session  
from django.contrib import messages
# Create your views here.

def home(request):
    return render(request,'index.html',{})

@login_required
def dashboard(request):
    # Get or create budget for the user
    budget, created = Budget.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Budget form handling
    if request.method == "POST" and "set_budget" in request.POST:
        budget_form = BudgetForm(request.POST, instance=budget)
        if budget_form.is_valid():
            budget_form.save()
            return redirect('dashboard')

    # Transaction form handling
    elif request.method == "POST" and "add_transaction" in request.POST:
        transaction_form = TransactionForm(request.POST)
        if transaction_form.is_valid():
            transaction = transaction_form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('dashboard')

    else:
        budget_form = BudgetForm(instance=budget)
        transaction_form = TransactionForm()

    # Ensure budget.amount is a float
    budget_amount = float(budget.amount) if budget.amount else 1  # Avoid division by zero

    # Convert all Decimal fields to float before calculations
    total_income = float(sum(float(t.amount) for t in transactions if t.type == "income"))
    total_expenses = float(sum(float(t.amount) for t in transactions if t.type == "expense"))
    
    # Calculate remaining budget
    remaining_budget = budget_amount - total_expenses

    # Calculate progress bar percentage
    progress = (total_expenses / budget_amount) * 100 if budget_amount > 0 else 0

    # Expense breakdown by category
    expense_categories = {}
    for t in transactions:
        if t.type == "expense":
            if t.category in expense_categories:
                expense_categories[t.category] += float(t.amount)
            else:
                expense_categories[t.category] = float(t.amount)

    categories = list(expense_categories.keys())
    amounts = list(expense_categories.values())

    return render(request, 'dashboard.html', {
        'budget_form': budget_form,
        'transaction_form': transaction_form,
        'transactions': transactions,
        'budget_amount': budget_amount,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'remaining_budget': remaining_budget,
        'progress': progress,
        'expense_categories': json.dumps(categories),
        'expense_amounts': json.dumps(amounts),
    })
   

def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    return redirect('dashboard')



load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@csrf_exempt
def ai_chat(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_query = data.get("query", "")

            if not user_query:
                return JsonResponse({"response": "Please enter a question."}, status=400)

            # Retrieve chat history from session
            chat_history = request.session.get("chat_history", [])

            # Send request to AI API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": user_query}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200}
            }

            response = requests.post(url, headers=headers, json=payload)
            result = response.json()

            # Debugging logs
            print("API Response:", result)

            # Extract AI response correctly
            ai_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Sorry, I could not generate a response.")

            # Clean response: Remove markdown symbols (*, #, -) and extra newlines
            clean_response = re.sub(r'[*#-]', '', ai_response)  # Removes *, #, and -
            clean_response = re.sub(r'\n+', '\n', clean_response).strip()  # Removes extra newlines

            # Append new messages to history
            chat_history.append({"role": "user", "message": user_query})
            chat_history.append({"role": "ai", "message": clean_response})

            # Save updated history in session
            request.session["chat_history"] = chat_history
            request.session.modified = True  # Ensure session updates

            return JsonResponse({"response": clean_response, "history": chat_history})

        except Exception as e:
            print("Error in ai_chat:", e)  # Debug error message
            return JsonResponse({"response": "Error processing your request."}, status=500)

    return JsonResponse({"response": "Invalid request method."}, status=400)



@csrf_exempt
def clear_chat(request):
    if request.method == "POST":
        request.session.pop("chat_history", None)  # Remove chat history from session
        request.session.modified = True
        return JsonResponse({"message": "Chat cleared successfully"})
    
    return JsonResponse({"error": "Invalid request method"}, status=400)


    
@login_required
def investment(request):
    return render(request,'investment.html',{})
@login_required
def learning(request):
    return render(request,'learning.html',{})

def loginuser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"Username: {username}, Password: {password}")  # Debugging

        user = authenticate(request, username=username, password=password)  # Authenticate user
        print(f"Authenticated User: {user}")  # Debugging

        if user is not None:
            login(request, user)  # Logs in user
            #print("Login successful!")
            return redirect('home')  
        else:
            messages.error(request,'Invalid username or password!')
            return redirect('loginuser')

    return render(request, 'login.html')


def signup(request):

    if request.method == "POST":

        form = SignUpForm(request.POST)

        if form.is_valid():

            user=form.save()
            login(request,user) # Automatically log in after signup
            return redirect('home')     # Redirect to the home page after signup
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def logoutuser(request):
    logout(request)
    return render(request,'index.html',{})

