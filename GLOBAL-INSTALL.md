# Check-list branchements/connections projet de fin d’année   
  
  
- S’assurer que tous les appareils soient connectés au même réseau (Cudy-FA5C : 58448069)  
- Connection SSH au Mac mini sur VScode(IP : 192.168.10.205) -> mdp : digital   
- Connection SSH au raspberryPi sur VScode (pi@pi1) -> mdp : raspberry,  IP: 192.168.10.127  
- Connection SSH terminal Mac mini :  ssh [digital@192.168.10.205](mailto:digital@192.168.10.205) / mdp : digital  
- Activer venv -> sur le Mac : cd Documents/projects/python-project puis lancer la commande source/bin/activate  
- Lancer LLM -> Lancer commande dans terminal Mac mini : llama-server -hf unsloth/functiongemma-270m-it-GGUF:Q4_K_M ou llama-server -m + emplacement du LLM  
- Lancer le server WSServer.py sur le raspberryPi puis lancer l’interface python (login.py) coté pc client
- Pour connecté ESP32 -> Via Thonny lancer l’ESP32  
  

## Branchement des capteurs 

Regarder dans les Classes dans l'esp32 pour avoir les numéros des pins pour les brancher correctement aux raspberryPi.
