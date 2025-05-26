#!/usr/bin/env python
"""
Script to generate database schema diagrams.
"""
import os
import sys
import subprocess
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare.settings')
django.setup()

def generate_er_diagram():
    """Generate ER diagram using django-extensions."""
    try:
        # Check if django-extensions is installed
        import django_extensions
    except ImportError:
        print("django-extensions is not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'django-extensions', 'pygraphviz'], check=True)
    
    # Add django_extensions to INSTALLED_APPS if not already there
    if 'django_extensions' not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS += ('django_extensions',)
    
    print("Generating ER diagram...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Generate diagram for all models
    subprocess.run([
        'python', 'manage.py', 'graph_models', '-a', 
        '-g', '-o', 'docs/er_diagram_all.png'
    ], check=True)
    
    # Generate diagram for specific apps
    subprocess.run([
        'python', 'manage.py', 'graph_models', 
        'patients', 'doctors', 'appointments', 
        '-g', '-o', 'docs/er_diagram_core.png'
    ], check=True)
    
    print("ER diagrams generated in docs/ directory.")

def generate_schema_sql():
    """Generate SQL schema."""
    print("Generating SQL schema...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Generate SQL schema
    with open('docs/schema.sql', 'w') as f:
        subprocess.run(['python', 'manage.py', 'sqlmigrate', 'patients', '0001'], stdout=f)
        f.write('\n\n')
        subprocess.run(['python', 'manage.py', 'sqlmigrate', 'doctors', '0001'], stdout=f)
        f.write('\n\n')
        subprocess.run(['python', 'manage.py', 'sqlmigrate', 'appointments', '0001'], stdout=f)
    
    print("SQL schema generated in docs/schema.sql")

def generate_model_documentation():
    """Generate model documentation."""
    print("Generating model documentation...")
    
    # Create output directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Get all models
    from django.apps import apps
    
    with open('docs/models.md', 'w') as f:
        f.write('# Database Models\n\n')
        
        for app_config in apps.get_app_configs():
            if app_config.name in ['patients', 'doctors', 'appointments', 'authenticator']:
                f.write(f'## {app_config.verbose_name}\n\n')
                
                for model in app_config.get_models():
                    f.write(f'### {model.__name__}\n\n')
                    f.write(f'{model.__doc__ or ""}\n\n')
                    
                    f.write('| Field | Type | Description |\n')
                    f.write('| ----- | ---- | ----------- |\n')
                    
                    for field in model._meta.fields:
                        field_type = field.get_internal_type()
                        help_text = getattr(field, 'help_text', '')
                        f.write(f'| {field.name} | {field_type} | {help_text} |\n')
                    
                    f.write('\n')
    
    print("Model documentation generated in docs/models.md")

def main():
    """Main function."""
    # Ensure we're in the project root directory
    if not os.path.exists('manage.py'):
        print("Error: This script must be run from the project root directory.")
        sys.exit(1)
    
    # Generate ER diagram
    try:
        generate_er_diagram()
    except Exception as e:
        print(f"Error generating ER diagram: {e}")
    
    # Generate SQL schema
    try:
        generate_schema_sql()
    except Exception as e:
        print(f"Error generating SQL schema: {e}")
    
    # Generate model documentation
    try:
        generate_model_documentation()
    except Exception as e:
        print(f"Error generating model documentation: {e}")
    
    print("Schema generation complete.")

if __name__ == '__main__':
    main()
