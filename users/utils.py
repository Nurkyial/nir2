from datetime import date
from base.models import Semester

class SemesterUtils:
    @staticmethod
    def get_or_create_current_semester():
        """
        Возвращает текущий семестр из базы данных или создает его, если он отсутствует.
        """
        today = date.today()
        year = today.year
        
        if 1 <= today.month <= 6: # Январь - Июнь
            semester_type = 'Spring'
            start_date = date(year, 2, 1)
            end_date = date(year, 6, 30)
        else: # Июль - Декабрь
            semester_type = 'Fall'
            start_date = date(year, 9, 1)
            end_date = date(year + 1, 1, 31)
        
        semester_name = f"{'Весенний семестр' if semester_type == 'Spring' else 'Осенний семестр'} {year}/{year if semester_type == 'Spring' else year + 1} учебного года"

        semester, created = Semester.objects.get_or_create(
            semester_name=semester_name,
            defaults={
                'semester_type': semester_type,
                'start_date': start_date,
                'end_date': end_date,
            }
        )

        return semester, created