document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".activation-form");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Captura el código de activación
        const otp = document.getElementById("activation_code").value.trim();

        if (!otp) {
            alert("Por favor, ingresa el código de activación.");
            return;
        }

        // Obtener el email del usuario previamente registrado
        // Puedes pasarlo por query params, localStorage o hidden input
        const email = localStorage.getItem("registro_email"); // ejemplo usando localStorage
        if (!email) {
            alert("No se encontró el correo del usuario. Vuelve a registrarte.");
            window.location.href = "registro.html";
            return;
        }

        try {
            const response = await fetch("https://img-users-90018350665.northamerica-south1.run.app/accounts/activar/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, otp })
            });

            const data = await response.json();

            if (response.ok && data.message === "Cuenta activada correctamente. Ya puedes iniciar sesión") {
                alert(data.message);
                window.location.href = "login.html";
            } else {
                let msg = data.message || "Código de activación incorrecto.";
                alert(msg);
            }

        } catch (error) {
            console.error("Error de conexión:", error);
            alert("Error de conexión con el servidor.");
        }
    });
});
