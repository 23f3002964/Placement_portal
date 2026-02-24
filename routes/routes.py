# routes/routes.py
from flask import Flask, render_template, request, redirect, url_for, session, flash

def setup_routes(app):
    # Authentication routes
    @app.route('/')
    def index():
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user_type = request.form.get('user_type', 'student')  # default to student if not provided
            
            # Here you would validate credentials against your database
            # For now, I'll simulate a simple validation
            if username and password:
                session['user'] = username
                session['user_type'] = user_type
                
                if user_type == 'student':
                    return redirect(url_for('student_dashboard'))
                elif user_type == 'company':
                    # Redirect to company dashboard (not implemented yet)
                    return redirect(url_for('index'))  # Redirect back to login for now
                elif user_type == 'admin':
                    return redirect(url_for('admin_dashboard'))
        
        # Pass an empty context since the template expects form fields
        return render_template('auth/login.html', form={})
    
    @app.route('/register')
    def register():
        return render_template('auth/register.html')
    
    @app.route('/register/student', methods=['GET', 'POST'])
    def register_student():
        if request.method == 'POST':
            # Process student registration
            # For now, just redirect to login
            flash('Student registered successfully!', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register_student.html')
    
    @app.route('/register/company', methods=['GET', 'POST'])
    def register_company():
        if request.method == 'POST':
            # Process company registration
            # For now, just redirect to login
            flash('Company registered successfully!', 'success')
            return redirect(url_for('login'))
        return render_template('auth/register_company.html')
    
    @app.route('/change-password', methods=['GET', 'POST'])
    def change_password():
        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if new_password == confirm_password:
                # Update password in database
                flash('Password changed successfully!', 'success')
                if session.get('user_type') == 'student':
                    return redirect(url_for('student_dashboard'))
                elif session.get('user_type') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('login'))
            else:
                flash('New passwords do not match!', 'error')
        
        return render_template('auth/change_password.html')
    
    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form['email']
            # Implement password reset logic here
            flash('Password reset link sent to your email!', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/forgot_password.html')
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # Return the app to indicate that routes have been set up
    return app