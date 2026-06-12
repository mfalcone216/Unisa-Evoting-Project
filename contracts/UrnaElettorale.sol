// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UrnaElettorale {
    
    // Struttura che rappresenta il pacchetto di voto salvato su Blockchain
    struct PacchettoVoto {
        string C;         // Voto cifrato in RSA-OAEP (Base64)
        string sigma;     // Firma di integrità dello studente in RSA-PSS (Base64)
        uint256 t_vote;   // Timestamp
        uint256 seq;      // Contatore di sequenza anti-replay
        string pk_u;      // Chiave pubblica effimera dello studente (PEM)
        bool exists;      // Flag per sapere se il T_ID ha già votato
    }

    // Il vero "Registro delle Urne": Mappa il T_ID (Token Anonimo) al Pacchetto
    mapping(string => PacchettoVoto) private registroUrna;
    
    // Array per memorizzare tutti i T_ID validi per lo scrutinio finale
    string[] private tuttiTID; 

    // Eventi pubblici per trasparenza (generano i log sulla blockchain)
    event VotoRegistrato(string t_id, uint256 seq);
    event VotoSovrascritto(string t_id, uint256 seq);

    // Funzione principale richiamata dai Nodi via Web3
    function sottomettiVoto(
        string memory _t_id,
        string memory _C,
        string memory _sigma,
        uint256 _t_vote,
        uint256 _seq,
        string memory _pk_u
    ) public {
        
        // Logica 1: Se il T_ID non ha mai votato, registriamo il voto
        if (!registroUrna[_t_id].exists) {
            registroUrna[_t_id] = PacchettoVoto(_C, _sigma, _t_vote, _seq, _pk_u, true);
            tuttiTID.push(_t_id);
            emit VotoRegistrato(_t_id, _seq);
        } 
        // Logica 2: Sovrascrittura Anti-Coercizione o Blocco Replay Attack
        else {
            // Require = Se la condizione è falsa, la transazione fallisce (Il Mago sconfitto)
            require(_seq > registroUrna[_t_id].seq, "REJECT_REPLAY_ATTACK: seq non valido");
            
            // Se seq è maggiore, sovrascriviamo il vecchio pacchetto (Il Padrino sconfitto)
            registroUrna[_t_id] = PacchettoVoto(_C, _sigma, _t_vote, _seq, _pk_u, true);
            emit VotoSovrascritto(_t_id, _seq);
        }
    }

    // Funzione per il Comitato di Scrutinio: Estrae tutti i voti cifrati validi a fine elezione
    function getTuttiVoti() public view returns (string[] memory) {
        string[] memory votiFinali = new string[](tuttiTID.length);
        for (uint i = 0; i < tuttiTID.length; i++) {
            votiFinali[i] = registroUrna[tuttiTID[i]].C;
        }
        return votiFinali;
    }
}