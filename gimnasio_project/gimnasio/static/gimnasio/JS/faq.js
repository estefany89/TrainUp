<script>
document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".faq-btn");
    const content = document.getElementById("faq-content");

    const textos = {
        entrenamiento: `
            <h4>Entrenamiento</h4>
            <p>Aquí encontrarás toda la información sobre los tipos de entrenamiento, rutinas y clases disponibles.</p>
        `,
        tarifas: `
            <h4>Tarifas</h4>
            <p>Consulta nuestros precios, membresías y métodos de pago.</p>
            <h4>Horario</h4>
            <p>Disponemos de un amplio horario para tu comodidad.</p>
        `,
        compromiso: `
            <h4>Compromiso del Usuario</h4>
            <p>Normas generales, condiciones de uso y responsabilidades dentro del gimnasio.</p>
        `
    };

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {

            // Cambiar botón activo
            buttons.forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            // Cambiar contenido
            const target = this.getAttribute("data-target");

            content.style.opacity = 0;

            setTimeout(() => {
                content.innerHTML = textos[target];
                content.style.opacity = 1;
            }, 200);
        });
    });
});
</script>