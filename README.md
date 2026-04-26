# ksef-send

Klient wysyłki faktur do KSeF.

Funkcje:

- walidacja XML FA
- business rules
- preview PDF przed wysyłką
- manifest wysyłki
- archiwizacja faktur
- obsługa numeru KSeF
- integracja z API KSeF 2.x / 3.0

Pipeline faktury:

pending → validated → approved → preview → sent → KSeF → archive