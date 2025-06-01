document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');

    form.addEventListener('submit', function (event) {
        const teacherAssigned = form.dataset.teacherAssigned === 'true';
        if (!teacherAssigned) {
            event.preventDefault();
            alert('Вы не можете добавить работу, пока не назначен научный руководитель.');
        }
    });
});
 