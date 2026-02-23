document.addEventListener("DOMContentLoaded", () => {
    const segments = document.querySelectorAll(".segment");

    segments.forEach(seg => {
        const segId = seg.getAttribute("data-segment");
        const hiddenInput = document.getElementById(`input_segment_${segId}`);

        // Инициализация цвета из значения инпута (если оно уже есть)
        if (hiddenInput) {
            seg.setAttribute("data-state", hiddenInput.value || "0");
        }

        seg.addEventListener("click", function() {
            // Получаем текущее состояние
            let currentState = parseInt(this.getAttribute("data-state") || 0);

            // Циклично меняем 0 -> 1 -> 2 -> 3 -> 0
            let newState = (currentState + 1) % 4;

            // Применяем новый цвет через CSS-атрибут
            this.setAttribute("data-state", newState);

            // Записываем в скрытый инпут для Django
            if (hiddenInput) {
                hiddenInput.value = newState;
            }
        });
    });
});