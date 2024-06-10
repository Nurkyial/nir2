from base.models import Submission

def user_profile_pk(request):
    context = {}
    if request.user.is_authenticated:
        user_profile_pk = request.user.userprofile.pk
        context['user_profile_pk'] = user_profile_pk
        
        student = request.user.userprofile
        submissions = Submission.objects.filter(assignment__student=student)
        context['submissions'] = submissions
        print(f"Submissions for {student}: {submissions}")  # Move this inside the if block
    else:
        context['user_profile_pk'] = None
        context['submissions'] = None
    return context

