# E-Voting System: Decentralized Consortium Blockchain
Progetto realizzato per il corso di *Algorithms and Protocols for Cybersecurity* (Università degli Studi di Salerno).

## Descrizione
Il sistema implementa un protocollo di E-Voting decentralizzato basato su:
- **Consortium Blockchain (EVM/Solidity)** per l'immutabilità del registro.
- **Autenticazione Federata (OpenID Connect)** per la gestione delle identità.
- **Crittografia Asimmetrica (RSA-OAEP/PSS)** per la confidenzialità e l'integrità del voto.

## Struttura del Progetto
- `/contracts`: Smart Contract (`UrnaElettorale.sol`) e interfacce ABI.
- `/idp_server`: Server Flask (OIDC) per l'autenticazione MFA.
- `/client_app`: Client Python per la cifratura client-side e sottomissione tramite Web3.

## Setup e Utilizzo
1. Avvia Ganache e configura il server RPC su `http://127.0.0.1:7545`.
2. Esegui `deploy.py` per caricare lo Smart Contract.
3. Avvia il server IdP: `python idp_server/server_oidc.py`.
4. Lancia il client di voto: `python client_app/elettore.py`.

## Sicurezza
Il sistema è progettato per mitigare attivamente:
- **Replay Attacks**: Tramite controllo di sequenza (`seq`).
- **Coercizione**: Tramite sovrascrittura protetta (`seq` monotono).
- **Insider Threat**: Tramite Threshold Secret Sharing (WP2).