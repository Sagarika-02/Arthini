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
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter,landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from reportlab.lib.styles import getSampleStyleSheet
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
            category = t.category.strip().lower()  # Normalize category names
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
   





# Export transaction logs as PDF

def export_transactions_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Transactions.pdf"'

    # Create a landscape-oriented PDF with more width
    pdf = SimpleDocTemplate(response, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    # Title
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Transaction Report</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))  # Space after title

    # Define table headers
    data = [["Category", "Description", "Amount (Rs.)", "Type", "Date"]]

    # Fetch user transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Calculate total income and expense
    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expense = sum(t.amount for t in transactions if t.type == "expense")

    # Add transactions to data
    for transaction in transactions:
        data.append([
            transaction.category,
            transaction.description,
            transaction.amount,
            transaction.type.capitalize(),
            transaction.date.strftime('%#d %B %Y')  # Date format: "3 March 2025"
        ])

    # Add total income & expense row
    data.append(["", "", "", "Total Income:", f"Rs. {total_income}"])
    data.append(["", "", "", "Total Expense:", f"Rs. {total_expense}"])

    # Create table
    table = Table(data, colWidths=[120, 220, 100, 100, 120])  # Set column width for better spacing

    # Add style to table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # White header text
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Align all text center
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold headers
        ('FONTSIZE', (0, 0), (-1, -1), 12),  # Bigger font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for headers
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Row background
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Borders for all cells
        ('LEFTPADDING', (0, 0), (-1, -1), 10),  # Padding left
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Padding right
        ('ROWBACKGROUNDS', (0, 1), (-1, -3), [colors.white, colors.white]),  # Alternate row colors
        ('BACKGROUND', (-2, -2), (-1, -1), colors.lightgrey),  # Background for total rows
        ('FONTNAME', (-2, -2), (-1, -1), 'Helvetica-Bold'),  # Bold total text
    ])


    
    table.setStyle(style)

    # Add table to elements
    elements.append(table)

    # Build PDF
    pdf.build(elements)
    return response


def generate_pdf(transactions):
    from io import BytesIO
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    
    p.setFont("Helvetica", 14)
    p.drawString(100, 800, "Transaction Log")
    y = 780

    for transaction in transactions:
        p.setFont("Helvetica", 10)
        p.drawString(100, y, f"{transaction.date} | {transaction.description} | {transaction.amount} | {transaction.type} | {transaction.category}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    return buffer




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

