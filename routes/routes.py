from flask import render_template, Blueprint, url_for, request, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import UserAccount, StudentProfile, CompanyProfile, PlacementDrive, Application, db

def setup_routes(app):
    main_bp = Blueprint('main', __name__)
    auth_bp = Blueprint('auth', __name__)
    admin_bp = Blueprint('admin', __name__)
    student_bp = Blueprint('student', __name__)
    company_bp = Blueprint('company', __name__)
    common_bp = Blueprint('common', __name__)

    @common_bp.route('/')
    def home():
        return render_template('common/home.html')

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            if current_user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif current_user.role == 'company':
                return redirect(url_for('company.dashboard'))
            elif current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = UserAccount.query.filter_by(username=username).first()
            if user and user.password == password:  # Note: No hashing used as requested
                if user.is_blacklisted:
                    flash('Your account has been blacklisted.', 'danger')
                    return redirect(url_for('auth.login'))
                if not user.is_active:
                    flash('Your account is inactive.', 'danger')
                    return redirect(url_for('auth.login'))
                    
                # Block pending companies
                if user.role == 'company':
                    profile = CompanyProfile.query.filter_by(user_id=user.id).first()
                    if profile and profile.approval_status != 'Approved':
                        flash(f'Your company account is currently {profile.approval_status}. Please wait for admin approval.', 'warning')
                        return redirect(url_for('auth.login'))
                        
                login_user(user)
                flash('Login successful!', 'success')
                
                # Redirect to appropriate dashboard based on role
                if user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                elif user.role == 'company':
                    return redirect(url_for('company.dashboard'))
                elif user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
                
        return render_template('auth/login.html')

    @common_bp.route('/register-options')
    def register_options():
        return render_template('common/register_options.html')

    @common_bp.route('/privacy')
    def privacy_policy(): return "Privacy Policy Placeholder"
    
    @common_bp.route('/terms')
    def terms_of_service(): return "Terms of Service Placeholder"

    @admin_bp.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        total_students = StudentProfile.query.count()
        total_companies = CompanyProfile.query.count()
        total_drives = PlacementDrive.query.count()
        total_applications = Application.query.count()
        
        pending_companies = CompanyProfile.query.filter_by(approval_status='Pending').count()
        pending_drives = PlacementDrive.query.filter_by(status='Pending').count()
        
        return render_template('admin/dashboard.html',
                               total_students=total_students,
                               total_companies=total_companies,
                               total_drives=total_drives,
                               total_applications=total_applications,
                               pending_companies=pending_companies,
                               pending_drives=pending_drives)

    @admin_bp.route('/manage-students')
    @login_required
    def manage_students():
        if current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        action = request.args.get('action')
        student_id = request.args.get('id')
        if action and student_id:
            student = StudentProfile.query.get_or_404(student_id)
            if action == 'blacklist':
                student.user_account.is_blacklisted = True
                flash(f'Student {student.user_account.username} blacklisted.', 'warning')
            elif action == 'unblacklist':
                student.user_account.is_blacklisted = False
                flash(f'Student {student.user_account.username} unblacklisted.', 'info')
            elif action == 'deactivate':
                student.user_account.is_active = False
                flash(f'Student {student.user_account.username} deactivated.', 'warning')
            elif action == 'activate':
                student.user_account.is_active = True
                flash(f'Student {student.user_account.username} activated.', 'info')
            db.session.commit()
            return redirect(url_for('admin.manage_students'))
            
        search_query = request.args.get('q', '')
        if search_query:
            students = StudentProfile.query.join(UserAccount).filter(
                (StudentProfile.branch.ilike(f'%{search_query}%')) |
                (UserAccount.username.ilike(f'%{search_query}%')) |
                (UserAccount.email.ilike(f'%{search_query}%'))
            ).all()
        else:
            students = StudentProfile.query.all()
            
        return render_template('admin/manage_students.html', students=students, search_query=search_query)

    @admin_bp.route('/manage-companies')
    @login_required
    def manage_companies():
        if current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        action = request.args.get('action')
        company_id = request.args.get('id')
        if action and company_id:
            company = CompanyProfile.query.get_or_404(company_id)
            if action == 'approve':
                company.approval_status = 'Approved'
                flash(f'Company {company.company_name} approved.', 'success')
            elif action == 'reject':
                company.approval_status = 'Rejected'
                flash(f'Company {company.company_name} rejected.', 'danger')
            elif action == 'blacklist':
                company.user_account.is_blacklisted = True
                flash(f'Company {company.company_name} blacklisted.', 'warning')
            elif action == 'unblacklist':
                company.user_account.is_blacklisted = False
                flash(f'Company {company.company_name} unblacklisted.', 'info')
            db.session.commit()
            return redirect(url_for('admin.manage_companies'))
            
        search_query = request.args.get('q', '')
        if search_query:
            companies = CompanyProfile.query.join(UserAccount).filter(
                (CompanyProfile.company_name.ilike(f'%{search_query}%')) |
                (UserAccount.email.ilike(f'%{search_query}%'))
            ).all()
        else:
            companies = CompanyProfile.query.all()
            
        return render_template('admin/manage_companies.html', companies=companies, search_query=search_query)

    @admin_bp.route('/manage-drives')
    @login_required
    def manage_drives():
        if current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        action = request.args.get('action')
        drive_id = request.args.get('id')
        if action and drive_id:
            drive = PlacementDrive.query.get_or_404(drive_id)
            if action == 'approve':
                drive.status = 'Approved'
                flash(f'Drive "{drive.job_title}" approved.', 'success')
            elif action == 'reject':
                drive.status = 'Rejected'
                flash(f'Drive "{drive.job_title}" rejected.', 'danger')
            elif action == 'delete':
                db.session.delete(drive)
                flash(f'Drive "{drive.job_title}" deleted permanently.', 'warning')
            db.session.commit()
            return redirect(url_for('admin.manage_drives'))
            
        drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
        return render_template('admin/manage_drives.html', drives=drives)

    @admin_bp.route('/view-applications')
    @login_required
    def view_applications():
        if current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        applications = Application.query.order_by(Application.application_date.desc()).all()
        return render_template('admin/view_applications.html', applications=applications)

    @student_bp.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        
        # Get applications
        applications = Application.query.filter_by(student_id=profile.id).all() if profile else []
        applied_drive_ids = [app.drive_id for app in applications]
        
        # Get available drives not yet applied to
        available_drives = PlacementDrive.query.filter(
            PlacementDrive.status == 'Approved',
            ~PlacementDrive.id.in_(applied_drive_ids) if applied_drive_ids else True
        ).all()
        
        return render_template('student/dashboard.html', 
                               available_drives=available_drives,
                               applications=applications,
                               profile=profile)

    @student_bp.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if current_user.role != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        import os
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        
        if request.method == 'POST':
            # Update regular fields
            profile.branch = request.form.get('branch')
            
            cgpa_str = request.form.get('cgpa')
            if cgpa_str:
                try:
                    profile.cgpa = float(cgpa_str)
                except ValueError:
                    pass
            
            # Handle resume upload
            if 'resume' in request.files:
                file = request.files['resume']
                if file.filename != '':
                    filename = secure_filename(f"{current_user.username}_{file.filename}")
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    profile.resume_path = f"uploads/resumes/{filename}"
            
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('student.profile'))
            
        return render_template('student/profile.html', profile=profile)

    @student_bp.route('/apply/<int:drive_id>', methods=['POST'])
    @login_required
    def apply(drive_id):
        if current_user.role != 'student':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Please complete your profile first.', 'warning')
            return redirect(url_for('student.profile'))
            
        # Check if already applied
        existing_app = Application.query.filter_by(student_id=profile.id, drive_id=drive_id).first()
        if existing_app:
            flash('You have already applied to this drive.', 'info')
        else:
            new_app = Application(student_id=profile.id, drive_id=drive_id, status='Applied')
            db.session.add(new_app)
            db.session.commit()
            flash('Successfully applied to the drive.', 'success')
            
        return redirect(url_for('student.dashboard'))

    @company_bp.route('/dashboard')
    @login_required
    def dashboard():
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        drives = PlacementDrive.query.filter_by(company_id=profile.id).all() if profile else []
        active_drives_count = sum(1 for d in drives if d.status == 'Approved')
        
        # Calculate total applications across all company's drives
        total_applications = 0
        if profile:
            drive_ids = [d.id for d in drives]
            total_applications = Application.query.filter(Application.drive_id.in_(drive_ids)).count()
            
        recent_activity = []
        if profile and drive_ids:
            recent_activity = Application.query.filter(
                Application.drive_id.in_(drive_ids)
            ).order_by(Application.application_date.desc()).limit(5).all()
        
        return render_template('company/dashboard.html', 
                               active_drives_count=active_drives_count,
                               total_applications=total_applications,
                               recent_activity=recent_activity)

    @company_bp.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        
        if request.method == 'POST':
            profile.company_name = request.form.get('company_name')
            profile.hr_contact = request.form.get('hr_contact')
            profile.website = request.form.get('website')
            
            db.session.commit()
            flash('Company profile updated successfully.', 'success')
            return redirect(url_for('company.profile'))
            
        return render_template('company/profile.html', profile=profile)

    @company_bp.route('/view-applications')
    @login_required
    def view_applications():
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Company profile incomplete', 'warning')
            return redirect(url_for('company.dashboard'))
            
        # Get all drives for this company
        drives = PlacementDrive.query.filter_by(company_id=profile.id).all()
        drive_ids = [d.id for d in drives]
        
        # Check if filtering by specific drive
        filter_drive_id = request.args.get('drive_id', type=int)
        
        # Get all applications for those drives
        query = Application.query.filter(Application.drive_id.in_(drive_ids))
        if filter_drive_id and filter_drive_id in drive_ids:
            query = query.filter_by(drive_id=filter_drive_id)
            
        applications = query.order_by(Application.application_date.desc()).all()
            
        return render_template('company/view_applications.html', applications=applications)

    @company_bp.route('/update-status/<int:app_id>', methods=['POST'])
    @login_required
    def update_application_status(app_id):
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        application = Application.query.get_or_404(app_id)
        
        # Security check: ensure the application belongs to a drive owned by this company
        if application.drive_details.company_id != profile.id:
            flash('Unauthorized action.', 'danger')
            return redirect(url_for('company.view_applications'))
            
        new_status = request.form.get('status')
        if new_status in ['Applied', 'Shortlisted', 'Selected', 'Rejected']:
            application.status = new_status
            db.session.commit()
            flash('Application status updated successfully.', 'success')
        else:
            flash('Invalid status provided.', 'danger')
            
        return redirect(url_for('company.view_applications'))

    @company_bp.route('/create-drive', methods=['GET', 'POST'])
    @login_required
    def create_drive():
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Company profile incomplete', 'warning')
            return redirect(url_for('company.dashboard'))
            
        if request.method == 'POST':
            job_title = request.form.get('job_title')
            job_description = request.form.get('job_description')
            eligibility_criteria = request.form.get('eligibility_criteria')
            application_deadline = request.form.get('application_deadline')
            
            from datetime import datetime
            deadline_date = None
            if application_deadline:
                try:
                    deadline_date = datetime.strptime(application_deadline, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid date format.', 'danger')
                    return redirect(url_for('company.create_drive'))
            
            # Create the drive. Defaults to Pending.
            new_drive = PlacementDrive(
                company_id=profile.id,
                job_title=job_title,
                job_description=job_description,
                eligibility_criteria=eligibility_criteria,
                application_deadline=deadline_date,
                status='Pending'
            )
            db.session.add(new_drive)
            db.session.commit()
            flash('Placement drive created successfully. It is pending admin approval.', 'success')
            return redirect(url_for('company.view_drives'))
            
        return render_template('company/create_drive.html')

    @company_bp.route('/view-drives')
    @login_required
    def view_drives():
        if current_user.role != 'company':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('common.home'))
            
        profile = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            flash('Company profile incomplete', 'warning')
            drives = []
        else:
            action = request.args.get('action')
            drive_id = request.args.get('id', type=int)
            if action and drive_id:
                drive = PlacementDrive.query.filter_by(id=drive_id, company_id=profile.id).first()
                if drive:
                    if action == 'close':
                        drive.status = 'Closed'
                        flash(f'Drive "{drive.job_title}" has been closed.', 'info')
                    elif action == 'delete':
                        db.session.delete(drive)
                        flash(f'Drive "{drive.job_title}" deleted permanently.', 'warning')
                    db.session.commit()
                return redirect(url_for('company.view_drives'))
                
            drives = PlacementDrive.query.filter_by(company_id=profile.id).order_by(PlacementDrive.created_at.desc()).all()
            
        return render_template('company/view_drives.html', drives=drives)

    @auth_bp.route('/change-password')
    def change_password(): return render_template('auth/change_password.html')

    @auth_bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('common.home'))

    @auth_bp.route('/register/student', methods=['GET', 'POST'])
    def register_student():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            branch = request.form.get('branch')
            
            existing_user = UserAccount.query.filter((UserAccount.username == username) | (UserAccount.email == email)).first()
            if existing_user:
                flash('Username or email already exists.', 'danger')
                return redirect(url_for('auth.register_student'))
                
            new_user = UserAccount(username=username, email=email, password=password, role='student')
            db.session.add(new_user)
            db.session.flush() # To get new_user.id
            
            new_profile = StudentProfile(user_id=new_user.id, branch=branch)
            db.session.add(new_profile)
            db.session.commit()
            
            flash('Student registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        return render_template('auth/register_student.html')

    @auth_bp.route('/register/company', methods=['GET', 'POST'])
    def register_company():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            company_name = request.form.get('company_name')
            hr_contact = request.form.get('hr_contact')
            website = request.form.get('website')
            
            existing_user = UserAccount.query.filter((UserAccount.username == username) | (UserAccount.email == email)).first()
            if existing_user:
                flash('Username or email already exists.', 'danger')
                return redirect(url_for('auth.register_company'))
                
            new_user = UserAccount(username=username, email=email, password=password, role='company')
            db.session.add(new_user)
            db.session.flush()
            
            new_profile = CompanyProfile(user_id=new_user.id, company_name=company_name, hr_contact=hr_contact, website=website)
            db.session.add(new_profile)
            db.session.commit()
            
            flash('Company registration successful. Pending admin approval.', 'success')
            return redirect(url_for('auth.login'))
            
        return render_template('auth/register_company.html')



    app.register_blueprint(common_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(main_bp)
