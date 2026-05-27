#!/usr/bin/env python
"""
Test script to verify the username uniqueness fix for StaffAddForm and StudentAddForm.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.forms import StaffAddForm, StudentAddForm
from accounts.models import User

def test_staff_form_username_generation():
    """Test that StaffAddForm generates unique usernames when not provided."""
    print("Testing StaffAddForm username generation...")
    
    # Test 1: Form with empty username should auto-generate
    form_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '123456789',
        'address': '123 Main St',
        'gender': 'M',
        'password1': 'testpassword123',
        'password2': 'testpassword123',
    }
    
    form = StaffAddForm(data=form_data)
    if form.is_valid():
        print("✓ Form is valid with empty username")
        print(f"  Generated username: {form.cleaned_data.get('username')}")
    else:
        print("✗ Form validation failed:")
        print(f"  Errors: {form.errors}")
    
    # Test 2: Form with duplicate username should raise error
    # First, create a user
    User.objects.create_user(
        username='jane.smith',
        email='jane@example.com',
        password='testpass123',
        first_name='Jane',
        last_name='Smith'
    )
    
    form_data2 = {
        'username': 'jane.smith',  # Duplicate
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane2@example.com',
        'phone': '987654321',
        'address': '456 Oak St',
        'gender': 'F',
        'password1': 'testpassword123',
        'password2': 'testpassword123',
    }
    
    form2 = StaffAddForm(data=form_data2)
    if not form2.is_valid() and 'username' in form2.errors:
        print("✓ Form correctly rejects duplicate username")
        print(f"  Error: {form2.errors['username']}")
    else:
        print("✗ Form should have rejected duplicate username")
    
    # Test 3: Form with existing username pattern should add number
    User.objects.create_user(
        username='john.doe',
        email='johndoe@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )
    
    form_data3 = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'johndoe2@example.com',
        'phone': '555555555',
        'address': '789 Elm St',
        'gender': 'M',
        'password1': 'testpassword123',
        'password2': 'testpassword123',
    }
    
    form3 = StaffAddForm(data=form_data3)
    if form3.is_valid():
        generated_username = form3.cleaned_data.get('username')
        if generated_username.startswith('john.doe') and generated_username != 'john.doe':
            print(f"✓ Form correctly generated numbered username: {generated_username}")
        else:
            print(f"✗ Generated username should be numbered: {generated_username}")
    else:
        print(f"✗ Form validation failed: {form3.errors}")

def test_student_form_username_generation():
    """Test that StudentAddForm generates unique usernames when not provided."""
    print("\nTesting StudentAddForm username generation...")
    
    from core.models import School, SchoolClass, Session, Term
    
    # Create necessary objects for student form
    school = School.objects.create(name='Test School')
    session = Session.objects.create(session='2024/2025')
    term = Term.objects.create(term='First Term', session=session)
    school_class = SchoolClass.objects.create(name='Class 1', school=school)
    
    form_data = {
        'first_name': 'Alice',
        'last_name': 'Wonder',
        'email': 'alice@example.com',
        'phone': '111222333',
        'address': 'Wonderland',
        'gender': 'F',
        'level': 'F1',
        'class_assigned': school_class.id,
        'password1': 'studentpass123',
        'password2': 'studentpass123',
    }
    
    form = StudentAddForm(data=form_data, school=school)
    if form.is_valid():
        print("✓ Student form is valid with empty username")
        print(f"  Generated username: {form.cleaned_data.get('username')}")
    else:
        print("✗ Student form validation failed:")
        print(f"  Errors: {form.errors}")

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Username Uniqueness Fix")
    print("=" * 60)
    
    # Clean up any existing test users
    User.objects.filter(username__in=['jane.smith', 'john.doe', 'john.doe1']).delete()
    
    test_staff_form_username_generation()
    test_student_form_username_generation()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)