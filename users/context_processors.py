from base.models import Submission, Assignment
from users.models import UserProfile

def user_profile_pk(request):
    context = {}
    if request.user.is_authenticated:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            if user_profile.role == 'student':
                submissions = Submission.objects.filter(assignment__student=user_profile)
                context = {
                    'user_profile_pk': user_profile.pk,
                    'submissions': submissions,
                    'assignments': None,
                    'role': 'student'
                }
            elif user_profile.role == 'teacher':
                assignments = Assignment.objects.filter(teacher=user_profile)
                context = {
                    'user_profile_pk': user_profile.pk,
                    'assignments': assignments,
                    'submissions': None,
                    'role': 'teacher'
                }
                
            elif user_profile.role == 'admin':
                assignments = Assignment.objects.filter(is_accepted=True)
                context = {
                    'user_profile_pk': user_profile.pk,
                    'assignments': assignments,
                    'submissions': None,
                    'role': 'admin'
                }
            else:
                context = {
                    'user_profile_pk': user_profile.pk,
                    'role': 'unknown'
                }
                
        except UserProfile.DoesNotExist:
            context = {
                'user_profile_pk': None,
                'role': 'unknown'
            }
    
    else:
        context = {
            'user_profile_pk': None,
            'role': 'guest'
        }
    return context
                



