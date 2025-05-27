from rest_framework import permissions

class IsPatient(permissions.BasePermission):
    
    #Custom permission to only allow patients to access their own data.
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'patient')
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has a patient attribute
        if hasattr(obj, 'patient'):
            return obj.patient.user == request.user
        # For Patient objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class IsDoctor(permissions.BasePermission):
    
    #Custom permission to only allow doctors to access their own data.
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'doctor')
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has a doctor attribute
        if hasattr(obj, 'doctor'):
            return obj.doctor.user == request.user
        # For Doctor objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

class IsPatientOrDoctor(permissions.BasePermission):
    
    #Custom permission to allow patients to access their own data and doctors to access data of their patients.
    
    def has_permission(self, request, view):
        return hasattr(request.user, 'patient') or hasattr(request.user, 'doctor')
    
    def has_object_permission(self, request, view, obj):
        # If user is a patient
        if hasattr(request.user, 'patient'):
            # Check if the object has a patient attribute
            if hasattr(obj, 'patient'):
                return obj.patient.user == request.user
            # For Patient objects
            if hasattr(obj, 'user'):
                return obj.user == request.user
        
        # If user is a doctor
        if hasattr(request.user, 'doctor'):
            # Check if the object has a doctor attribute
            if hasattr(obj, 'doctor'):
                return obj.doctor.user == request.user
            # For appointments, check if the doctor is assigned to the appointment
            if hasattr(obj, 'doctor_id'):
                return obj.doctor_id == request.user.doctor.id
            # For medical records, check if the doctor created the record
            if hasattr(obj, 'doctor_id') and hasattr(obj, 'patient_id'):
                return obj.doctor_id == request.user.doctor.id
        
        return False

class IsAdminUser(permissions.BasePermission):
    
    #Custom permission to only allow admin users to access the view.
    
    def has_permission(self, request, view):
        return request.user and request.user.is_staff
