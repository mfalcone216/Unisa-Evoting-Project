async function aggiornaSmartphone() {
    try {
        const response = await fetch('/api/totp');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('phone-totp').innerText = data.totp;
            document.getElementById('phone-time').innerText = data.expires_in;
        }
    } catch (e) {
        document.getElementById('phone-totp').innerText = "ERROR";
    }
}
// Aggiorna lo schermo del telefono ogni secondo
setInterval(aggiornaSmartphone, 1000);
aggiornaSmartphone();

async function effettuaLogin() {
    const matricola = document.getElementById('matricola').value;
    const totp = document.getElementById('totp').value;
    const errorDiv = document.getElementById('login-error');
    const btn = document.getElementById('btn-login');

    errorDiv.innerText = "";
    btn.innerText = "Verifica OIDC in corso...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matricola, totp })
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('login-section').classList.add('hidden');
            document.getElementById('voting-section').classList.remove('hidden');
            // Nascondiamo il finto smartphone una volta loggati
            document.getElementById('smartphone').style.display = 'none';
        } else {
            errorDiv.innerText = "Errore: " + data.message;
        }
    } catch (error) {
        errorDiv.innerText = "Server disconnesso.";
    } finally {
        btn.innerText = "Accedi in Sicurezza";
        btn.disabled = false;
    }
}

async function sottomettiVoto() {
    // Raccogliamo il Vettore delle Scelte dai 4 menù a tendina
    const voto_sa = document.getElementById('voto_sa').value;
    const voto_cda = document.getElementById('voto_cda').value;
    const voto_cdd = document.getElementById('voto_cdd').value;
    const voto_adisurc = document.getElementById('voto_adisurc').value;

    // Creiamo l'array JSON formattato come stringa (Payload Crittografico)
    const vettorePreferenze = JSON.stringify([voto_sa, voto_cda, voto_cdd, voto_adisurc]);

    const errorDiv = document.getElementById('vote-error');
    const btn = document.getElementById('btn-vota');

    errorDiv.innerText = "";
    btn.innerText = "Cifratura OAEP e Sottomissione Web3...";
    btn.disabled = true;

    try {
        const response = await fetch('/api/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preferenze: vettorePreferenze })
        });
        const data = await response.json();

        if (response.ok) {
            document.getElementById('voting-section').classList.add('hidden');
            document.getElementById('receipt-section').classList.remove('hidden');
            document.getElementById('receipt-block').innerText = data.block;
            document.getElementById('receipt-gas').innerText = data.gas;
            document.getElementById('receipt-hash').innerText = data.tx_hash;
        } else {
            errorDiv.innerText = "Errore: " + data.message;
        }
    } catch (error) {
        errorDiv.innerText = "Impossibile comunicare con Ganache.";
    } finally {
        btn.innerText = "Cifra Vettore e Invia Voto";
        btn.disabled = false;
    }
}