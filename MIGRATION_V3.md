# Migration dwarf_python_api vers l'API V3 du Dwarf (remplacement complet)

Ce document remplace la premiere version : sur demande, V3 REMPLACE V2 dans
ce repo (pas de coexistence des deux jeux de `.proto` dans le meme
processus Python - ils partagent des noms de fichiers/symboles et
collisionnent dans le pool de descripteurs protobuf).

## Ce qui a change concretement dans le zip fourni

- `dwarf_python_api/proto/*.proto` et `*_pb2.py` : **entierement remplaces**
  par le jeu de `.proto` du fork `dwarfAlp` (client V3 valide sur materiel
  reel), recompiles avec `protoc` (`grpcio-tools`, compatible
  `protobuf>=4.25.8` deja requis par ce repo).
- `dwarf_python_api/lib/websockets_utils.py` :
  - 2 constantes d'erreur moteur renommees dans le nouveau proto ont ete
    mises a jour partout ou elles etaient utilisees :
    `CODE_STEP_MOTOR_LIMIT_POSITION_HITTED` -> `CODE_STEP_MOTOR_LIMIT_POSITION_HIT`,
    `CODE_STEP_MOTOR_POSITION_NEED_RESET` -> `CODE_STEP_MOTOR_NEED_RESET`.
    (Verifie : ce sont les 2 SEULES constantes utilisees dans ce fichier a
    avoir change de nom entre l'ancien proto et celui de dwarfAlp - tout le
    reste, y compris `CMD_SYSTEM_SET_MASTERLOCK`, est identique ou alias.)
  - Ajout de l'import `task_center_pb2` (nouveau module MODULE_DEVICE_CONFIG).
  - Ajout de 4 nouveaux blocs de reception (meme patron que les blocs
    existants) pour reconnaitre les reponses aux commandes du handshake V3 :
    `CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO` (16405),
    `CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_MODE` (16402),
    `CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA` (16404),
    `CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_TECH` (16403).
- `dwarf_python_api/lib/dwarf_utils.py` : 6 nouvelles fonctions ajoutees
  juste apres `set_HostMaster()` (voir plus bas).
- `test_connect_v3.py` (racine) : script manuel pour valider la sequence de
  connexion avec un vrai Dwarf, dans l'esprit de `dwarf_test_apiV2`.

Tout le reste du repo (astro_dwarf_session cote appelant, get_config_data.py,
ftp_utils.py, etc.) n'a pas ete touche.

## Ce qui n'a PAS change (bonne nouvelle)

- Le transport bas niveau (`connect_socket`, `send_socket_message`,
  `DwarfWebSocketClient`) est inchange : meme port 9900, meme enveloppe
  `WsPacket`, meme mecanique de queue de resultats.
- `set_HostMaster()` / `unset_HostMaster()` sont inchanges : le mecanisme
  MASTER/SLAVE (`CMD_SYSTEM_SET_MASTER`, alias de l'ancien
  `CMD_SYSTEM_SET_MASTERLOCK`, meme valeur 13004) existe toujours cote
  protocole et le code qui le gere (a la fois la reponse `ComResponse` et la
  notification `CMD_NOTIFY_WS_HOST_SLAVE_MODE`) fonctionne pour les deux cas
  de figure observes chez `dwarfAlp`.
- Toutes les fonctions ASTRO existantes (`perform_goto`, `perform_calibration`,
  `perform_takeAstroPhoto`, etc.) continuent a utiliser les memes messages
  protobuf : le module ASTRO (3) est une extension additive, rien n'a ete
  supprime ni renomme dedans.

## Ce qui remplace le point bloquant historique (MASTER/SLAVE + ouverture camera)

En V2 : `set_HostMaster()` puis `perform_open_camera()` (CMD_CAMERA_TELE_OPEN_CAMERA,
10000) etaient necessaires avant que les commandes suivantes ne repondent.

En V3, d'apres l'implementation de reference `dwarfAlp` (testee sur
materiel), la sequence devient :

```
set_HostMaster()                      # inchange (module SYSTEM, 13004)
        |
perform_switch_shooting_mode(mode=8)  # NOUVEAU - module DEVICE_CONFIG, 16402
        |
perform_enter_camera()                # NOUVEAU - 16404, "initialiser la camera"
        |
perform_switch_shooting_tech(tech=2)  # NOUVEAU - 16403 (Deep Sky / stacking)
        |
perform_set_preview_quality(1)        # NOUVEAU - 10050 (best effort)
```

Ces 4 etapes sont enchainees par la nouvelle fonction
`perform_enter_astro_mode()` dans `dwarf_utils.py`. `perform_open_camera()`
(V2, module CAMERA_TELE) reste disponible mais dwarfAlp ne l'utilise plus
comme etape de bootstrap pour les appareils V3 - a garder en tete si vous
avez du code qui en dependait pour "debloquer" la connexion.

## A tester en premier avec dwarf_test_apiV2 / test_connect_v3.py

1. `set_HostMaster()` — doit toujours fonctionner comme avant.
2. `perform_get_device_state_info()` — purement informatif, bon moyen de
   verifier que le dialogue MODULE_DEVICE_CONFIG passe.
3. `perform_switch_shooting_mode(8)` — verifier le `shooting_mode_id` retourne.
4. `perform_enter_camera()` — **c'est l'etape critique** ("initialiser la
   camera"). Si ca bloque ici, capturer la trame Wireshark pour comparer
   avec ce qu'envoie l'appli officielle a ce moment precis.
5. `perform_switch_shooting_tech(2)`.
6. `perform_set_preview_quality(1)` — non bloquant si ca echoue, mais a
   verifier quand meme (cmd 10050 est une commande "APK 3.4.1 registry" pas
   encore confirmee sur tous les modeles).

## Points a garder en tete / a confirmer sur votre materiel

- Les valeurs `mode=8` et `tech=2` viennent de `dwarfAlp` (observees sur son
  materiel de test). Si votre Dwarf (modele different ?) renvoie un
  `shooting_mode_id` different de 8 apres `SWITCH_SHOOTING_MODE`, ou si
  `ENTER_CAMERA` renvoie un `shooting_mode_id` de 2 au lieu de 8 (dwarfAlp
  accepte les deux comme valides), ce n'est pas forcement une erreur -
  loggez et ajustez au besoin.
- `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` (10050) est traite comme "best
  effort" dans `perform_enter_astro_mode()` : je n'ai pas de confirmation
  independante de dwarfAlp sur son caractere strictement necessaire.
- Le `minor_version` envoye dans `WsPacket` reste a `1` partout dans le code
  existant (comportement V2 inchange) : je n'ai pas trouve de preuve dans
  dwarfAlp que le firmware V3 exige `WS_MINOR_VERSION_V3 (20)` pour
  fonctionner - a verifier empiriquement si le handshake echoue de maniere
  suspecte.

## Prochaines etapes proposees

Une fois la connexion validee :
1. GOTO + stacking (one-click GOTO, module ASTRO 11013/11014/11015 + reponse
   `ResOneClickGoto` + notification `CMD_NOTIFY_STATE_ASTRO_ONE_CLICK_GOTO`).
2. Calibration V3.
3. `camera_params` (module 15, nouveau style exposition/gain).
4. `v3_focus`, `v3_system` (GPS).

Je continuerai etape par etape, chacune testee avant d'enchainer, comme pour
cette premiere etape de connexion.

## Photo simple (non-astro) - module ajoute

`dwarfAlp` ne couvre pas ce mode (c'est un driver dedie a l'astro), donc il
n'y a pas d'implementation de reference a copier ici comme pour la connexion.

**Constat verifie** : les messages protobuf du module CAMERA_TELE
(`ReqOpenCamera`, `ReqGetAllParams`, `ReqSetAllParams`, `ResGetAllParams`,
`ReqPhoto`, etc.) sont identiques, champ pour champ, entre le proto V2 et
celui de `dwarfAlp`. Le nouveau module MODULE_DEVICE_CONFIG (14) semble
concerner uniquement l'arbitrage d'acces exclusif camera/moteur pour le
pipeline ASTRO (`task_center.proto` definit des `ExclusiveTaskType`
CAMERA/MOTOR/FOCUS_MOTOR/...), pas la photo simple.

**Hypothese a valider sur votre materiel** (`test_photo_simple_v3.py`) :
apres `set_HostMaster()`, les fonctions V2 existantes
(`perform_open_camera`, `perform_get_all_camera_setting`,
`perform_update_camera_setting`, `perform_takePhoto`) fonctionnent SANS
passer par `perform_enter_astro_mode()`.

**Ajout cote diagnostic** : le bloc de reception de
`CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO` dans `websockets_utils.py` affiche
desormais en clair (niveau `log.notice`) la liste `shooting_mode_and_techs`
renvoyee par l'appareil - c'est-a-dire les couples
`(shooting_mode, shooting_techs[])` que l'appareil connait reellement. C'est
la source la plus fiable pour identifier, empiriquement, la valeur de
`shooting_mode` correspondant a la photo simple (8 = astro, confirme par
dwarfAlp ; la valeur "photo" est probablement une autre entree de cette
liste - a lire dans les logs plutot qu'a deviner).

Deroule de `test_photo_simple_v3.py` :
1. `set_HostMaster()` puis `perform_get_device_state_info()` (regarder les
   logs pour `shooting_mode_and_techs`).
2. Chemin V2 direct : `perform_open_camera()` -> `perform_get_all_camera_setting()`
   -> `perform_update_camera_setting("exposure", "1/1000")` -> `perform_takePhoto()`.
3. Si l'etape 2 echoue/timeout : reessayer en ajoutant
   `perform_switch_shooting_mode(<valeur identifiee a l'etape 1>)` avant
   `perform_open_camera()` (la fonction existe deja, generique, cote
   connexion astro - reutilisable ici avec une autre valeur de mode).

Dites-moi ce que vous observez (en particulier le contenu de
`shooting_mode_and_techs` et a quelle etape ca bloque le cas echeant) et
j'ajusterai le code en consequence plutot que de deviner a l'aveugle.

## Connexion Bluetooth (comme dans dwarf_test_apiV2)

Ajout de `connect_bluetooth_cmd.py` a la racine : equivalent du mode
`--cmd` de `connect_bluetooth.py` (dwarf_test_apiV2), pour etablir la
connexion Bluetooth -> WiFi et ecrire l'IP/dwarf_id/dwarf_uid dans
`config.ini` (via `dwarf_python_api.get_config_data.update_config_data`),
AVANT de lancer `test_connect_v3.py` ou `test_photo_simple_v3.py` qui
en ont besoin pour savoir a quelle IP se connecter.

Verifie : le protocole BLE de provisioning WiFi (`dwarf_python_api.proto.ble_pb2`)
est inchange entre V2 et le nouveau proto - tous les champs/messages
utilises par `dwarf_ble_connect/` existent a l'identique.

Usage :
```
python connect_bluetooth_cmd.py --ssid "MonWifi" --pwd "monmotdepasse"
python test_connect_v3.py
python test_photo_simple_v3.py
```

Note environnement : `dwarf_ble_connect/lib/connect_direct_bluetooth.py`
importe `tkinter` de maniere inconditionnelle (meme si ce script ne
l'utilise pas en mode `--cmd`, c'est un heritage du code existant, non
modifie ici). Sur Linux, installez-le si besoin :
`sudo apt install python3-tk` (Debian/Ubuntu) ou l'equivalent pour votre
distribution.

### Mode web (confirme fonctionnel a l'identique)

Le mode web (`dwarf_ble_connect/connect_bluetooth.py`, appele via
`connect_bluetooth_web()`) - serveur HTTP local + pairing BLE via l'API Web
Bluetooth du navigateur (JS dans `dist_js/`) - ne depend d'aucun module
`dwarf_python_api.proto.*` cote Python : c'est un simple serveur HTTP qui
sert la page web et reecrit `config.ini` via les memes appels
`update_config_data(...)`. Il n'a donc pas ete touche par le remplacement
V2 -> V3, ce qui explique qu'il continue de fonctionner a l'identique
(confirme par test manuel).

### Correctif : `'FieldDescriptor' object has no attribute 'label'`

Bug pre-existant dans le repo d'origine, sans rapport avec le remplacement
du proto V2 -> V3 : il vient de la version de `protobuf` installee. Le
backend C (`upb`) des versions recentes de `protobuf` (verifie avec
`protobuf==7.34.1`) n'expose plus l'attribut `.label` sur
`google._upb._message.FieldDescriptor` (qui reste par contre acceessible
comme constante de classe, d'ou l'erreur uniquement a l'usage de
`descriptor.label`, pas de `descriptor.LABEL_REPEATED`).

Corrige dans `dwarf_ble_connect/lib/dwarf_protocol_ble.py`
(`fill_defaults_from_class` / `dict_with_defaults`) :
`descriptor.label == descriptor.LABEL_REPEATED` remplace par
`descriptor.is_repeated` (propriete booleenne equivalente, stable entre
versions de `protobuf`). Verifie qu'aucun autre endroit du repo n'utilise
`.label`/`LABEL_*`.

## Support Dwarf Mini (BLE)

Integre vos mises a jour de `dwarf_lib_ble.py` et `connect_dwarf.html` :
- Nouvel UUID de service `DWARFMINI_SERVICE_UUID = 0000daf5-...` (cote
  Python et cote HTML/JS), `device_dwarf_id = 4` pour "Dwarf Mini".
- Detection du SSID de point d'acces `DWARF_mini_...` en plus de
  `DWARF3_...` dans la logique de provisioning WiFi (les deux fichiers).
- (Le fichier HTML que vous avez fourni contenait vos identifiants WiFi
  personnels en dur dans `BleSTASSIDDwarf`/`BleSTAPWDDwarf` - je les ai
  remis a vide dans la version livree ici, par prudence, a renseigner vous-
  meme localement si vous utilisez ce fichier HTML directement.)

Coherence verifiee avec `dwarfAlp/device_profile.py` : `ws_device_id=4` y
est bien utilise pour "Dwarf mini" (et pour "Dwarf 3" egalement - voir
section suivante, ce n'est pas un identifiant de modele mais une valeur de
protocole commune a toute la famille V3).

## Correctif important : `major_version`/`minor_version`/`device_id` du WsPacket

En creusant `dwarfAlp/device_profile.py` (`ProtocolProfile` de Dwarf 3 ET
Dwarf mini, toutes deux famille `"v3"`), j'ai trouve la confirmation directe
qui manquait dans la premiere version de ce document :

```python
ws_major_version=1,
ws_minor_version=20,   # <- WS_MINOR_VERSION_V3, PAS 1 comme en V2
ws_device_id=4,         # <- PAS 1 (ancienne valeur "DWARF II" codee en dur)
```

Le code herite de la V2 envoyait `major_version=1, minor_version=1,
device_id=1` sur CHAQUE message (`send_message` et `send_message_init`
dans `websockets_utils.py`). C'est corrige : les deux endroits utilisent
maintenant `minor_version=20` et `device_id=4`, conformement a ce que
`dwarfAlp` envoie reellement sur du materiel V3.

**C'est potentiellement significatif pour vos essais de connexion** : si le
firmware V3 verifie strictement ces champs (ce qui est plausible vu qu'un
enum dedie `WS_MINOR_VERSION_V3 = 20` a ete ajoute au protocole), les
envoyer a 1 au lieu de 20 pourrait expliquer un echec silencieux ou un
comportement degrade la ou vous avez teste jusqu'ici.

Note : `ws_client_id` differe par modele chez dwarfAlp
(`0000DAF3-...` pour Dwarf 3, `0000DAF4-...` pour Mini), mais ceci concerne
le champ `WsPacket.client_id`, qui dans ce repo reste une valeur libre lue
depuis `config.ini` (`CLIENT_ID`) - je n'ai pas trouve de preuve que le
firmware l'exploite comme un identifiant de modele attendu, donc je ne l'ai
pas touche. A garder en tete si un probleme de connexion resiste malgre
les corrections ci-dessus.

## Correctif majeur : renommage systematique de `notify.proto`

En testant la connexion, vous avez trouve : `module
'dwarf_python_api.proto.notify_pb2' has no attribute 'ResNotifySDcardInfo'`.

En verifiant systematiquement (pas juste ce cas), il s'avere que **les 14
classes `notify.ResNotifyXxx` utilisees dans `websockets_utils.py` ont ete
renommees** dans le proto `dwarfAlp` : le prefixe `ResNotify` a ete
supprime partout. Sans ce correctif, la boucle de reception aurait plante
en silence (rattrapee par le `try/except` generique de `receive_messages`,
qui logue "Unhandled exception" et continue) a chaque nouvelle notification
du firmware, une par une, au fil de vos tests.

| Ancien nom (V2) | Nouveau nom (V3) | Remarque |
|---|---|---|
| `ResNotifySDcardInfo` | `StorageInfo` | champ `code` supprime (log adapte) |
| `ResNotifyHostSlaveMode` | `HostSlaveMode` | inchange |
| `ResNotifyStateAstroGoto` | `AstroGotoState` | gagne `target_name` (corrige un bug latent en V2 : le code y accedait deja alors que le champ n'existait pas dans l'ancien proto) |
| `ResNotifyStateAstroCalibration` | `AstroCalibrationState` | inchange |
| `ResNotifyStateAstroTracking` | `AstroTrackingState` | inchange |
| `ResNotifyRgbState` | `RgbState` | inchange |
| `ResNotifyPowerIndState` | `PowerIndState` | inchange |
| `ResNotifyTemperature` | `Temperature` | inchange |
| `ResNotifyStreamType` | `StreamType` | inchange |
| `ResNotifyEqSolvingState` | `EqSolvingState` | perd le champ `step` et l'enum imbrique `Action` (log simplifie, ne garde que `state`) |
| `ResNotifyProgressCaptureRawLiveStacking` | `ProgressCaptureRawLiveStacking` | champ `update_count_type` renomme `update_type` |
| `ResNotifyFocus` | `FocusPosition` | champ `focus` renomme `pos` |
| `ResNotifyOperationState` | `OperationStateNotify` | inchange |
| `ResNotifyCamFunctionState` | `PhotoState` | approximation : le champ `function_id` (V2) a disparu, remplace par plusieurs messages typés par fonction (`PhotoState`, `BurstState`, `RecordState`, ...) tous de forme identique `{state, camera_type}`. Le code ne lisant que `.state`, `PhotoState` fait l'affaire pour l'instant sur `CMD_NOTIFY_TELE_FUNCTION_STATE`/`CMD_NOTIFY_WIDE_FUNCTION_STATE`, mais ce n'est pas garanti etre le message exact que le firmware V3 envoie sur ces commandes precises - a surveiller si un comportement etrange apparait sur la fin de prise de photo. |

Verifie de maniere exhaustive : plus aucune classe `notify.*`, `base__pb2.*`,
`camera.*`, `astro.*`, `motor.*`, `rgb.*`, `task_center.*` utilisee dans
`websockets_utils.py` ne manque dans le nouveau proto (verification faite
sur l'ensemble du fichier, pas seulement sur le cas remonte).

## MASTER LOCK : probablement vestigial sur les appareils V3

Vous avez constate un timeout total sur `set_HostMaster()` (aucune reponse,
ni `ComResponse` ni notification `HostSlaveMode`), alors que d'autres
commandes (ouverture camera wide, envoyee automatiquement a la connexion)
avaient deja recu une reponse valide juste avant - preuve que le transport
fonctionne, le probleme est specifique a `CMD_SYSTEM_SET_MASTER` (13004).

En reverifiant `dwarfAlp` : leur propre `_ensure_master_lock()` catch tout
echec (timeout inclus) SANS jamais bloquer la suite de la connexion - il
logue juste un warning. La seule chose conditionnee sur son succes est un
appel purement informatif (`GetDeviceStateInfo`). Rien dans leur code ne
suggere que le MASTER LOCK soit une precondition stricte pour la suite en
V3 - le mecanisme semble avoir ete supplante par l'arbitrage d'acces
exclusif par ressource du nouveau `MODULE_DEVICE_CONFIG`
(`ExclusiveTaskType` CAMERA/MOTOR/FOCUS_MOTOR/... dans `task_center.proto`).

**Correctif** : `test_connect_v3.py` et `test_photo_simple_v3.py` ne
s'arretent plus si `set_HostMaster()` echoue/timeout - ils logguent un
avertissement et continuent avec la suite de la sequence. Le transport
websocket lui-meme n'est pas affecte par ce timeout particulier (le
watchdog d'inactivite de `websockets_utils.py` est reinitialise a chaque
nouvel envoi de commande, MASTER LOCK ou pas).

A confirmer sur votre materiel : si la suite de la sequence (device config
/ camera) fonctionne malgre l'absence de reponse au MASTER LOCK, on pourra
purement et simplement retirer cet appel de la sequence V3 dans une
prochaine iteration plutot que de le tenter en pure perte a chaque connexion.

## Sequence V3 confirmee fonctionnelle sur materiel reel (Dwarf Mini)

Test complet reussi : `SWITCH_SHOOTING_MODE(8)` -> `mode=8`,
`ENTER_CAMERA` -> `mode=8`, `SWITCH_SHOOTING_TECH(2)` -> `tech=2`. Le
MASTER LOCK a bien timeout sans bloquer la suite, comme prevu.

Bruit de fond observe (sans gravite) pendant le changement de mode : de
nombreuses notifications `CMD_NOTIFY_GENERAL_INT_PARAM` (15264),
`CMD_NOTIFY_SWITCH_SHOOTING_MODE` (15267), `CMD_NOTIFY_WB` (15270,
balance des blancs) et `CMD_NOTIFY_CMOS_TEMPERATURE` (15292) arrivent en
rafale - normal (la camera se reconfigure), pas encore decodees par le
dispatcher (juste logguees brutes en "Receiving command NNNN"), non
bloquant. A decoder proprement dans une prochaine iteration si on veut des
logs plus propres ou exploiter ces donnees (temperature capteur, etc.).

## Decouverte empirique : mode photo simple = mode 1

Le diagnostic `shooting_mode_and_techs` obtenu sur la Dwarf Mini reelle :

```
mode=1  parent=-1  techs=[1, 3, 4, 5]
mode=2  parent=-1  techs=[2]
mode=3  parent=-1  techs=[2, 3, 4, 5]
mode=4  parent=-1  techs=[2, 5]
mode=5  parent=-1  techs=[2]
mode=8  parent=3   techs=[2, 3, 4, 5]   <- ASTRO, confirme
mode=9  parent=3   techs=[2, 3, 4, 5]
mode=10 parent=3   techs=[2, 3, 4, 5]
```

`mode=1` (racine comme le mode 8, pas une variante d'un autre mode) avec
des techniques `[1,3,4,5]` correspond tres vraisemblablement au mode photo
simple, les valeurs de tech correspondant a photo/burst/video/timelapse
(recoupement avec un indice trouve plus tot dans `dwarfii_api`, devine a
tort pour une autre commande a l'epoque, mais probablement juste ici).

Ajoute dans `dwarf_utils.py` :
- `SHOOTING_MODE_PHOTO = 1`, `SHOOTING_TECH_PHOTO = 1`
- `perform_enter_shooting_mode(mode, tech)` : fonction generique factorisee
  (mode switch + enter camera + tech switch + preview quality)
- `perform_enter_astro_mode()` devient un simple appel a
  `perform_enter_shooting_mode(8, 2)` (comportement inchange, confirme OK)
- `perform_enter_photo_mode()` : nouveau, appelle
  `perform_enter_shooting_mode(1, 1)` - **pas encore teste sur materiel
  reel**, hypothese la plus solide dont on dispose actuellement.

`test_photo_simple_v3.py` mis a jour pour utiliser `perform_enter_photo_mode()`
avant d'ouvrir la camera/prendre la photo (fonctions V2 inchangees ensuite).

## Confirme sur materiel reel : mode=1/tech=1 = photo simple

Test complet reussi : `SWITCH_SHOOTING_MODE(1)` -> `mode=1`,
`ENTER_CAMERA` -> `mode=1`, `SWITCH_SHOOTING_TECH(1)` -> `tech=1`. L'hypothese
est donc confirmee : le mode photo simple (sur table, sans astro) est bien
`mode=1, tech=1`, exactement le meme comportement que `mode=8, tech=2` pour
l'astro.

## Correctif : `CMD_CAMERA_TELE_SET_PREVIEW_QUALITY` (10050) jamais decodee

Le log a revele que cette commande, envoyee en fin de
`perform_enter_shooting_mode()` (etape "best effort"), n'avait aucun bloc de
reception associe dans le dispatcher : `connect_socket()` attendait donc
betement 30 secondes (timeout) a chaque appel, pour rien, a chaque entree
en mode astro OU photo. Corrige en ajoutant le meme patron de decodage
`ComResponse` que pour `CMD_CAMERA_TELE_OPEN_CAMERA` (reponse generique
`{code}`). A confirmer que le firmware repond bien maintenant sous un delai
normal plutot que de toujours timeout (si le firmware ne repond
effectivement jamais a cette commande specifique, le decodage correct ne
change rien au timeout - dans ce cas il vaudra mieux retirer cet appel de
la sequence par defaut).

## Analyse d'une capture reseau reelle (PCAPdroid, session "photo normale")

Vous avez fourni un `.pcap` capture avec PCAPdroid (tPacketCapture ne
fonctionnait pas a cause du VPN) d'une session complete avec l'appli
officielle : connexion, mode photo, reglages exposition/gain, prise de
photo. Analyse faite directement avec `scapy` (reassemblage du flux TCP
port 9900, parsing manuel des frames WebSocket RFC6455, puis decodage
protobuf avec le proto V3 deja compile dans ce repo).

**Confirme :**
- `mode=1, tech=1` = photo simple (deja teste manuellement, confirme ici
  independamment par le trafic reel de l'appli officielle).
- `ENTER_CAMERA` : `client_param.encode_type=1` (deja implemente correctement).
- L'appli officielle **n'appelle jamais** `CMD_CAMERA_TELE_OPEN_CAMERA`
  (10000, l'ancienne "ouverture camera" V2) dans cette session : l'entree
  en mode (`SWITCH_SHOOTING_MODE` + `ENTER_CAMERA` + `SWITCH_SHOOTING_TECH`)
  suffit. `test_photo_simple_v3.py` ne l'appelle donc plus.
- Prise de photo : `CMD_CAMERA_TELE_PHOTOGRAPH` (10002), strictement
  inchangee par rapport a la V2 (`perform_takePhoto()` fonctionne tel quel).
  Suivi de la notification `CMD_NOTIFY_PHOTO_STATE` : `RUNNING` puis retour
  a l'etat par defaut (serialise vide en protobuf = `OPERATION_STATE_IDLE`)
  une fois la photo terminee.

**Decouverte majeure - exposition/gain (module CAMERA_PARAMS, 15) :**

L'appli officielle utilise `CMD_PARAM_SET_EXPOSURE` (16700) et
`CMD_PARAM_SET_GAIN` (16701), PAS les anciennes commandes V2
(`CMD_CAMERA_TELE_SET_EXP_MODE`/`SET_EXP`/`SET_GAIN_MODE`/`SET_GAIN`,
module CAMERA_TELE). Chaque parametre est identifie par un `param_id` sur
64 bits :

```
Photo (tele) exposition : param_id = 0x0101000000000001, mode=1, value=102 puis 111
Photo (tele) gain        : param_id = 0x0101000000000002, mode=1, value=50
Astro        exposition : param_id = 0x0201000000000001  (dwarfAlp)
Astro        gain        : param_id = 0x0201000000000002  (dwarfAlp)
```

Motif observe (2 points de donnees confirmes + dwarfAlp pour l'astro) :
l'octet de poids fort distingue le contexte (`0x01`=photo normal,
`0x02`=astro), le dernier octet le type de parametre (`...01`=exposition,
`...02`=gain). Pas confirme pour la camera wide (aucune donnee capturee).
Le champ `mode=1` observe dans les deux cas est probablement "manuel" (a
l'image de l'ancien `ReqSetExpMode.mode=1` en V2).

**Non elucide** : l'unite exacte du champ `value` (102, 111 pour l'exposition ; 50 pour le gain). Ce n'est vraisemblablement plus un index dans les tables `AllowedExposures`/`AllowedGains` de l'ancien `data_utils.py` (V2) - la plage semble differente. A affiner avec d'autres captures en notant la valeur affichee dans l'appli au moment de la capture.

**Ajoute dans `dwarf_utils.py`** : `perform_set_exposure_v3(value, param_id,
mode)` et `perform_set_gain_v3(value, param_id, mode)`, avec les 4
constantes `PARAM_ID_PHOTO_TELE_EXPOSURE`/`PARAM_ID_PHOTO_TELE_GAIN`/
`PARAM_ID_ASTRO_EXPOSURE`/`PARAM_ID_ASTRO_GAIN`. Reponse decodee dans le
dispatcher (`ComResponse` generique, meme patron que
`CMD_CAMERA_TELE_SET_PREVIEW_QUALITY`).

`test_photo_simple_v3.py` mis a jour pour suivre fidelement la sequence
observee : entree en mode photo -> `perform_set_exposure_v3(102)` ->
`perform_set_gain_v3(50)` -> `perform_takePhoto()`.

Pas de burst/video dans cette capture (session arretee apres les photos) -
a capturer separement si besoin.

## Elucide : signification exacte de "value" pour exposition et gain

Grace a vos reglages precis rapportes ("expo passee de auto a 0.5s", "gain
passe de 60 a 50"), recoupes avec la table `AllowedExposures`/`AllowedGains`
deja presente dans `data_utils.py` :

**Exposition** : `value` est exactement le meme INDEX que l'ancienne table
V2 `AllowedExposures`/`AllowedExposuresD3` - PAS la valeur en secondes.
Verifie par calcul : `get_exposure_index_by_name("0.5")` renvoie bien `111`
et `get_exposure_index_by_name("1/4")` renvoie bien `102` - exactement les
deux valeurs observees dans la capture (la premiere valeur, 102/"1/4", est
probablement un palier intermediaire traverse en passant de "Auto" a "0.5",
ou la valeur precedente encore active). **La table V2 est donc toujours
valide en V3**, juste exploitee via une nouvelle commande.

**Gain** : `value` est la valeur AFFICHEE directement (ex: `50` pour "50"),
PAS l'index de l'ancienne table `AllowedGains` (ou "50" est a l'index 15,
"60" a l'index 18). Confirme : vous etes passe de 60 a 50 dans l'appli,
valeur envoyee = 50 = valeur affichee directement, sans passer par la table.

**Ajoute dans `dwarf_utils.py`** :
- `perform_set_exposure_v3(value, param_id, mode)` : par index brut
  (compatibilite/tests bas niveau).
- `perform_set_exposure_by_name_v3(name, dwarf_id, param_id, mode)` :
  **a utiliser en priorite** - regle par nom lisible ("0.5", "1/1000",
  "1/30", ...), reutilise `get_exposure_index_by_name()` (data_utils.py,
  inchange) pour calculer le bon index automatiquement.
- `perform_set_gain_v3(value, param_id, mode)` : valeur directe (pas de
  version "by_name" necessaire, le gain n'a pas besoin de table de
  correspondance en V3).

`test_photo_simple_v3.py` mis a jour pour utiliser
`perform_set_exposure_by_name_v3("0.5")` (plus lisible que l'index brut) et
`perform_set_gain_v3(50)`.

## Confirme sur materiel reel : pipeline photo simple complet, de bout en bout

Test integral reussi sans aucune erreur : MASTER LOCK (timeout non
bloquant) -> SWITCH_SHOOTING_MODE(1)->1 -> ENTER_CAMERA->1 ->
SWITCH_SHOOTING_TECH(1)->1 -> SET_PREVIEW_QUALITY->0 (repond desormais
instantanement grace au correctif du dispatcher, plus de timeout de 30s) ->
SET_EXPOSURE->0 -> SET_GAIN->0 -> CMD_CAMERA_TELE_PHOTOGRAPH ("Continue OK",
confirme par les notifications CMD_NOTIFY_PHOTO_STATE qui suivent).

Le mode "photo simple" (hors astro) est donc entierement fonctionnel en V3
sur la Dwarf Mini : connexion, entree en mode photo, reglage exposition/
gain, prise de photo.

## Correctif : la fin de prise de vue (photo/burst/video/timelapse) n'etait jamais detectee

Vous avez remonte : la photo se prend bien (confirme visuellement : 0.5s,
gain 50), mais `perform_takePhoto()` ne se termine jamais - le script reste
bloque indefiniment apres le "Continue OK CMD_CAMERA_TELE_PHOTOGRAPH".

**Cause** : le code V2 attendait la notification `CMD_NOTIFY_TELE_FUNCTION_STATE`
(15215) pour detecter la fin de la prise de vue (etat `IDLE` = termine). Or
le firmware V3 envoie desormais une commande de notification DEDIEE par
technique, jamais `CMD_NOTIFY_TELE_FUNCTION_STATE` :

```
CMD_NOTIFY_PHOTO_STATE     = 15273   (photo, tech=1)
CMD_NOTIFY_BURST_STATE     = 15274   (burst, tech=3)
CMD_NOTIFY_RECORD_STATE    = 15275   (video, tech=4)
CMD_NOTIFY_TIMELAPSE_STATE = 15276   (timelapse, tech=5)
```

Ca correspond exactement aux 4 techniques disponibles sous `shooting_mode=1`
(`shooting_techs=[1,3,4,5]`) vu dans le diagnostic `shooting_mode_and_techs`.
Ces commandes de notification arrivaient bien (visibles dans vos logs comme
"Receiving command 15273", non decodees), mais aucun code ne les
reconnaissait comme la fin attendue de `CMD_CAMERA_TELE_PHOTOGRAPH` -> le
script attendait donc une notification qui n'arriverait jamais.

**Corrige** dans `websockets_utils.py` :
- Ajout des 4 nouvelles paires dans `VALID_PAIRS` (`CMD_CAMERA_TELE_PHOTOGRAPH`
  / `CMD_NOTIFY_PHOTO_STATE`, `CMD_CAMERA_TELE_BURST` / `CMD_NOTIFY_BURST_STATE`,
  `CMD_CAMERA_TELE_START_RECORD` / `CMD_NOTIFY_RECORD_STATE`,
  `CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO` / `CMD_NOTIFY_TIMELAPSE_STATE`).
- Ajout de 4 blocs de decodage (meme patron que l'ancien bloc
  `CMD_NOTIFY_TELE_FUNCTION_STATE`, conserve pour compatibilite au cas ou),
  utilisant les bons messages (`PhotoState`, `BurstState`, `RecordState`,
  `TimeLapseState`, tous de forme `{state, camera_type}`) et le bon enum
  (`OPERATION_STATE_IDLE`/`OPERATION_STATE_RUNNING`, plus correct que
  `ASTRO_STATE_*` utilise par erreur dans l'ancien code - meme valeurs
  numeriques donc pas de regression, juste plus juste semantiquement).

Anticipe pour la suite (burst/video/timelapse, prevu dans votre prochaine
session de test) puisque le meme bug se serait reproduit a l'identique sur
ces 3 techniques.

**Limite connue, non geree pour l'instant** : si les cameras tele ET wide
prennent une photo en meme temps, `CMD_NOTIFY_PHOTO_STATE` ne distingue les
deux que par le champ `camera_type` (non verifie dans le code actuel, qui
accepte n'importe quelle transition IDLE comme "termine"). Non bloquant pour
un usage tele seul (votre cas actuel), a revisiter si vous pilotez les deux
cameras simultanement.

## Confirme sur materiel reel : pipeline photo simple complet et fiable

Test final reussi de bout en bout sans aucun blocage :
`CMD_CAMERA_TELE_PHOTOGRAPH` -> "Starting" (etat RUNNING) -> "Success TAKE
PHOTO OK" (etat IDLE, via `CMD_NOTIFY_PHOTO_STATE`) -> deconnexion propre.
Le correctif ci-dessus resout completement le blocage. Le mode "photo
simple" en V3 (Dwarf Mini) est valide integralement : connexion, entree en
mode photo, reglage exposition/gain, prise de photo, detection de fin.















## Correctif : date de photo erronee (2038) - horloge jamais synchronisee

Vous avez remarque que la date des photos prises via les scripts de test
etait fausse (2038 - signe classique d'une horloge non synchronisee /
valeur sentinelle proche du depassement Y2038 sur un timestamp 32 bits).

**Cause** : la capture reseau de l'appli officielle montre qu'elle envoie
`CMD_SYSTEM_SET_TIME` (13000) et `CMD_SYSTEM_SET_TIME_ZONE` (13001) tout au
debut de chaque session, avant meme `GET_DEVICE_STATE_INFO`. Nos scripts de
test ne le faisaient pas : l'horloge interne du Dwarf n'etait donc jamais
mise a jour et restait sur sa valeur par defaut/erronee.

Bonne nouvelle : `perform_time()` et `perform_timezone()` existaient deja
dans `dwarf_utils.py` (V2, inchangees - `ReqSetTime`/`ReqSetTimezone` sont
identiques champ pour champ entre V2 et le proto `dwarfAlp`), il manquait
juste l'appel dans nos scripts.

**Corrige** :
- `test_connect_v3.py` et `test_photo_simple_v3.py` appellent maintenant
  `perform_time()` + `perform_timezone()` juste apres le MASTER LOCK,
  reproduisant l'ordre observe chez l'appli officielle.
- Bug latent corrige au passage dans `perform_timezone()` : si `TIMEZONE`
  n'est pas defini dans `config.ini`, `read_timezone()` renvoie `None`, et
  assigner `None` a un champ protobuf `string` levait une `TypeError` non
  geree (`bad argument type for built-in operation`). La fonction verifie
  desormais ce cas et logue un avertissement au lieu de planter.

## Lecture des parametres (exposition/gain) : pas de GET en V3, mecanisme de push

Vous avez remarque a raison que la lecture des parametres n'utilisait pas
encore la meme approche "complete" que l'ecriture. Analyse de la capture
reseau : l'appli officielle n'appelle **jamais** `CMD_CAMERA_TELE_GET_ALL_PARAMS`
(10036, l'ancienne commande V2) - et `param.proto` (module CAMERA_PARAMS)
ne definit d'ailleurs aucun message `ReqGetXxx`, seulement des `ReqSetXxx`.

**Le mecanisme V3 est un push, pas un request/response** : le firmware
diffuse spontanement la valeur courante de chaque parametre via des
notifications `CMD_NOTIFY_GENERAL_INT_PARAM` (15264), a l'entree en mode et
a chaque changement. Decode dans la capture (tele, mode photo) :

```
param_id=0x0101000000000001  mode=0  value=75    <- exposition AUTO (index de "1/30", la valeur par defaut)
param_id=0x0101000000000004  mode=0  value=0     <- parametre non identifie
param_id=0x0101000000000005  mode=0  value=0     <- parametre non identifie
param_id=0x0101000000000006  mode=0  value=0     <- parametre non identifie
param_id=0x0101000000000007  mode=0  value=0     <- parametre non identifie
param_id=0x0101000000000008  mode=0  value=30    <- parametre non identifie
param_id=0x0101100000000001  mode=0  value=75    <- meme jeu pour la camera WIDE (voir ci-dessous)
...
param_id=0x0101000000000001  mode=1  value=111   <- exposition apres reglage manuel ("0.5")
param_id=0x0101000000000002  mode=1  value=50    <- gain apres reglage manuel
```

Structure du `param_id` affinee (8 octets) : `[contexte][groupe][camera][000000][index]`
- octet 0 : contexte (`0x01`=photo, `0x02`=astro)
- octet 1 : groupe de parametres (`0x01` = groupe exposition/gain/etc.)
- octet 2 : camera (`0x00`=tele, `0x10`=wide)
- octet 7 : index du parametre dans le groupe (`0x01`=exposition, `0x02`=gain,
  `0x04`-`0x08` non identifies - possibles candidats : balance des blancs,
  contraste, saturation, nettete, anti-flicker - a confirmer)

Le champ `mode` du message confirme le meme sens que l'ancien
`ReqSetExpMode.mode` de la V2 : `0`=auto (valeur reportee par l'algorithme
de l'appareil), `1`=manuel (valeur explicitement fixee).

**Implemente** :
- `websockets_utils.py` : cache `client_instance.cameraParamsDwarf` (dict
  `param_id -> {mode, value}`), alimente par un nouveau bloc de decodage de
  `CMD_NOTIFY_GENERAL_INT_PARAM`. Expose aussi dans `get_client_status()`
  (cle `CameraParamsDwarf`) pour coherence avec les autres valeurs "poussees"
  deja gerees de la meme maniere (batterie, stockage, focus, etc.).
- `get_camera_param_v3(param_id)` (websockets_utils.py) : accesseur direct
  au cache (pas de requete reseau, lecture pure).
- `perform_read_exposure_v3(param_id, dwarf_id)` / `perform_read_gain_v3(param_id)`
  (dwarf_utils.py) : lecture cote appelant, avec conversion index->nom pour
  l'exposition (reutilise `get_exposure_name_by_index()`, table V2 inchangee).
  Retournent `None` si rien n'a encore ete recu (pas de mode entre depuis la
  connexion).
- `PARAM_ID_PHOTO_WIDE_EXPOSURE`/`PARAM_ID_PHOTO_WIDE_GAIN` ajoutes par
  symetrie du motif observe - **non confirmes** par un reglage explicite
  sur la camera wide dans la capture actuelle, a valider.

`test_photo_simple_v3.py` mis a jour pour illustrer la lecture juste apres
l'entree en mode (valeurs par defaut/auto) et juste apres les reglages
manuels (verification que le cache reflete bien le changement).

**A savoir** : comme c'est un cache alimente de maniere asynchrone,
`perform_read_exposure_v3()`/`perform_read_gain_v3()` peuvent renvoyer la
valeur precedente (ou `None`) si appeles immediatement apres
`perform_set_exposure_*`/`perform_set_gain_v3()`, avant que la notification
de confirmation n'ait eu le temps d'arriver - laisser une petite marge
(quelques centaines de ms) avant de lire, comme fait dans le script de test.

## Capture reseau complete : autofocus, 5 parametres image, video, burst, timelapse

Nouvelle capture reseau (session complete : autofocus, reglage des 5
parametres visibles dans l'appli - Luminosite/Contraste/Teinte/Saturation/
Accentuation -, photo, video, rafale, timelapse interrompu). Decodee avec
le meme pipeline (`scapy` + parsing WS manuel + proto V3).

### Les 5 parametres "inconnus" sont resolus, confirmes par vos captures d'ecran

```
param_id=0x0101000000000004  value=58   -> Luminosite  (ecran : 58)
param_id=0x0101000000000005  value=52   -> Contraste   (ecran : 52)
param_id=0x0101000000000006  value=56   -> Saturation  (ecran : 56)
param_id=0x0101000000000007  value=-88  -> Teinte      (ecran : -88)
param_id=0x0101000000000008  value=68   -> Accentuation/Nettete (ecran : 68)
```

Tous passent par `CMD_PARAM_SET_GENERAL_INT_PARAM` (16703, module
CAMERA_PARAMS) avec `param.ReqSetGeneralIntParam{param_id, value}` (pas de
champ `mode` ici, contrairement a exposition/gain/WB). Le champ `value` est
un `int32` signe - confirme par la Teinte a `-88`.

### Balance des blancs : commande 16702, non nommee dans le proto dwarfAlp

`CMD_PARAM_SET_WB = 16702` (trou de reverse engineering chez dwarfAlp,
identifie ici par sa position sequentielle - juste apres SET_GAIN=16701,
juste avant SET_GENERAL_INT_PARAM=16703 - et sa structure qui decode
proprement en `ReqSetWb{param_id, mode, value}`). Observe : `param_id`
= `0x0101000000000003` (suite logique de exposition=...01, gain=...02),
`mode=2`, `value=2` au moment ou l'appli affichait "Fluorescent" - l'ordre
exact des presets (Auto/Fluorescent/Incandescent/...) n'est pas confirme au-
dela de cette seule valeur.

### Autofocus

`CMD_FOCUS_AUTO_FOCUS` (15000, module MODULE_FOCUS=8), requete
`ReqNormalAutoFocus` (vide, `data_len=0` confirme) - distincte de
`ReqAstroAutoFocus` utilisee en astro. Reponse `ComResponse` generique. La
nouvelle position de mise au point arrive ensuite via
`CMD_NOTIFY_FOCUS_POSITION` (deja gere par le cache existant
`FocusValueDwarf`).

### Video, burst, timelapse : confirmes fonctionnels, avec leurs reglages

Sequence observee : `SWITCH_SHOOTING_TECH` est rappelee **avant chaque
nouvelle technique** (1=photo, puis 4=video, puis 3=burst, puis
5=timelapse) - ce n'est donc pas un choix fait une fois pour toutes a la
connexion, mais a repeter a chaque changement de type de prise de vue.

- **Video** : `CMD_CAMERA_TELE_START_RECORD`/`STOP_RECORD` (10005/10006,
  deja geres). Notification `CMD_NOTIFY_RECORD_TIME` (15286,
  `{record_time}` en secondes, compteur croissant pendant l'enregistrement).
- **Burst** : `CMD_CAMERA_TELE_BURST` (10003) puis, nouveau,
  `CMD_CAMERA_TELE_STOP_BURST` (10004, non mentionne jusqu'ici). Un reglage
  est envoye juste avant (`PARAM_ID_BURST_SETTING = 0x0102f00000000016`,
  valeur observee=2) mais **la semantique exacte n'est pas confirmee** :
  le burst execute a produit 3 photos (`CMD_NOTIFY_BURST_PROGRESS.total_count=3`),
  donc ce n'est probablement pas "nombre de photos" directement - plutot un
  index de preset (rafale courte/moyenne/longue ?). Notification
  `CMD_NOTIFY_BURST_PROGRESS` (15285, `{total_count, completed_count}`).
- **Timelapse** : `CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO`/`STOP_TIMELAPSE_PHOTO`
  (10033/10034, deja geres). Deux reglages envoyes juste avant :
  `PARAM_ID_TIMELAPSE_INTERVAL = 0x0102f00000000019` (**confirme** :
  derniere valeur envoyee = 4, qui correspond exactement au champ
  `interval` des notifications `CMD_NOTIFY_TIMELAPSE_OUT_TIME` recues
  pendant l'execution) et `PARAM_ID_TIMELAPSE_DURATION = 0x0102f0000000001a`
  (valeurs observees 2400/0/120, unite non confirmee - duree totale
  probable, en secondes). Notification `CMD_NOTIFY_TIMELAPSE_OUT_TIME`
  (15287, `{interval, total_time}`, `total_time` incremente au fil du
  timelapse).

### Ajoute dans dwarf_utils.py

`perform_auto_focus_v3()`, `perform_set_wb_v3()`,
`perform_set_image_param_v3()` (generique) + wrappers nommes
`perform_set_brightness_v3()`/`perform_set_contrast_v3()`/
`perform_set_saturation_v3()`/`perform_set_hue_v3()`/`perform_set_sharpness_v3()`,
`perform_set_burst_setting_v3()` (semantique a confirmer),
`perform_set_timelapse_interval_v3()`/`perform_set_timelapse_duration_v3()`.
Dispatcher (`websockets_utils.py`) : nouveaux blocs de decodage pour
`CMD_FOCUS_AUTO_FOCUS`, `CMD_PARAM_SET_WB` (16702) et
`CMD_PARAM_SET_GENERAL_INT_PARAM` (16703).

### Reste a confirmer si vous refaites une capture

- Ordre exact des presets de balance des blancs (Auto/Fluorescent/
  Incandescent/Lumiere du jour/...).
- Semantique precise de `PARAM_ID_BURST_SETTING` (tester plusieurs valeurs
  et noter le nombre de photos resultant pour chacune).
- Unite de `PARAM_ID_TIMELAPSE_DURATION` (secondes ? nombre de prises ?).

## Fichiers officiels data_utils.ts / data_dwarf3_config.ts fournis : cle de decodage complete

Vous avez fourni le code source JS/TS officiel de l'appli (`data_utils.ts` +
`data_dwarf3_config.ts`) qui construit les listes d'options affichees a
l'ecran (exposition, gain, balance des blancs, filtre IR, rafale, timelapse).
Ca a permis de confirmer/corriger plusieurs points en une fois.

### Confirme : exposition = index de table, gain = valeur brute

Recoupement avec la table officielle (identique a celle deja portee en
Python) : confirme que le protocole V3 envoie bien l'`index` de la table
pour l'exposition (102/111 = index de "1/4"/"0.5") et la valeur AFFICHEE
directement pour le gain (50 = "50", pas son index 15 dans la table). Pas
de changement de code necessaire ici, juste confirmation independante.

### Nouveau : table balance des blancs (Kelvin) et filtre IR

- `AllowedWBTemp` (data_utils.py) : table Kelvin officielle (2800K a 7500K,
  46 paliers). Concerne le mode "temperature manuelle" de la balance des
  blancs - le mode "preset" (Fluorescent/Incandescent/...) semble utiliser
  un encodage separe, non couvert par cette table (un seul point de donnee
  confirme : mode=2/value=2 correspondait a "Fluorescent" dans la capture
  precedente - ordre complet des presets non confirme).
- `AllowedIRFilter` : **"VIS Filter"(0) / "Astro Filter"(1) / "Duo-Band Filter"(2)**,
  3 options seulement. Nouvelle fonction `perform_set_ir_filter_v3(name_or_index)`,
  qui reutilise `CMD_CAMERA_TELE_SET_IRCUT` (10031, V2 inchangee, deja geree
  par `perform_update_camera_setting("IR", ...)`).

### Correctif important : le reglage "burst" identifie precedemment est probablement l'INTERVALLE, pas le NOMBRE de photos

La table officielle "Burst count" (featureParams id=3) a pour **valeur par
defaut l'index 0 = "3" photos** - exactement le nombre de photos produit
par le burst captured (`CMD_NOTIFY_BURST_PROGRESS.total_count=3`), *sans
qu'aucun reglage n'ait ete envoye pour ce parametre precis pendant cette
session*. Ca signifie que `PARAM_ID_BURST_SETTING` (valeur observee=2)
n'est tres probablement PAS le nombre de photos, mais **l'intervalle entre
les photos** ("Burst interval", featureParams id=9, table
`Off/1s/2s/3s/.../60s`) - la valeur 2 correspond exactement a "2 s" **si le
protocole V3 envoie les secondes brutes plutot que l'index de table** (voir
point suivant). Le vrai param_id du nombre de photos en rafale n'est pas
encore identifie.

`perform_set_burst_setting_v3()` renomme conceptuellement en assumant
l'intervalle (docstring mise a jour), et `perform_set_burst_interval_by_name_v3(name)`
ajoutee pour regler par nom ("2 s", etc.).

### Confirme : timelapse (intervalle ET duree) envoie des secondes brutes, pas un index de table

En recoupant les tables officielles avec les valeurs capturees :
- `PARAM_ID_TIMELAPSE_INTERVAL`, derniere valeur envoyee = 4 -> correspond
  a "4 s" (table `AllowedTimelapseInterval`) SI on interprete "4" comme des
  secondes brutes (l'index de table pour "4 s" serait 9, pas 4). Confirme
  independamment par le champ `interval=4` des notifications
  `CMD_NOTIFY_TIMELAPSE_OUT_TIME`.
- `PARAM_ID_TIMELAPSE_DURATION`, valeurs observees 2400/0/120 -> 2400s =
  "40 min", 120s = "2 min" (table `AllowedTimelapseTotalTime`), tous les
  deux des choix valides de la table officielle. 0 correspondrait
  probablement a "\u221e" (illimite).

**Conclusion** : contrairement a l'exposition (qui utilise l'index de
table), les parametres burst/timelapse (famille de param_id 0x0102...)
semblent utiliser directement la valeur reelle en secondes, pas un index
de table. Chaque parametre du protocole V3 a donc sa propre convention -
pas de regle unique, a verifier au cas par cas.

Ajoute dans `data_utils.py` : `get_timelapse_interval_seconds_by_name()`,
`get_timelapse_totaltime_seconds_by_name()`, `get_burst_interval_seconds_by_name()`
- convertissent un nom lisible ("4 s", "2 min", "\u221e") en secondes
brutes attendues par le protocole V3. Et dans `dwarf_utils.py` :
`perform_set_timelapse_interval_by_name_v3(name)`,
`perform_set_timelapse_duration_by_name_v3(name)`,
`perform_set_burst_interval_by_name_v3(name)` - a utiliser de preference
aux versions par valeur brute.

Toutes les nouvelles fonctions/tables sont verifiees par recalcul exact
contre les valeurs de la capture reseau (4, 2400, 120, 2 -> tous
retrouves a l'identique via les fonctions by_name).

## Capture reseau dediee "burst 20s / 5 images" + traces moteur : resolu

### Burst : nombre de photos ET intervalle desormais tous les deux confirmes

```
param_id=0x0102f00000000016  value=20   <- intervalle (confirme precedemment, "20 s")
param_id=0x0102f00000000015  value=4    <- nombre de photos (nouveau, essai intermediaire)
param_id=0x0102f00000000015  value=5    <- nombre de photos (valeur finale, "5 images")
```

`PARAM_ID_BURST_COUNT = 0x0102f00000000015` (nouveau, juste avant
`PARAM_ID_BURST_INTERVAL` dans la numerotation) confirme : la encore, valeur
BRUTE (5 = 5 photos), pas l'index de la table `AllowedBurstCount` (ou "5"
est a l'index 3). Coherent avec la convention "valeur brute" deja etablie
pour toute la famille burst/timelapse (contrairement a l'exposition qui
utilise l'index de table).

Renomme `PARAM_ID_BURST_SETTING` -> `PARAM_ID_BURST_INTERVAL` (alias
conserve pour compatibilite). Ajoute `perform_set_burst_count_v3(count)` et
`perform_set_burst_interval_v3(seconds)`.

### Balance des blancs : sequence de presets testee, mode confirme

```
mode=2  value=0
mode=2  value=1
mode=2  value=2   <- confirme precedemment = "Fluorescent"
mode=2  value=3
```

Confirme : `mode=2` = mode "preset" (par opposition a une temperature Kelvin
manuelle). 4 presets disponibles (0 a 3), mais seul l'un d'eux
("Fluorescent" = 2) a un nom confirme par une capture d'ecran - l'ordre
exact des 3 autres (probablement Auto/Incandescent/Daylight ou similaire)
reste a confirmer si vous voulez le nom exact de chaque valeur.

### Bonus : pilotage moteur au joystick decouvert

Le pave directionnel de l'appli (glisser-deposer, different des fleches
pas-a-pas) envoie `CMD_STEP_MOTOR_SERVICE_JOYSTICK` (14006, deja gere par
le dispatcher existant) en RAFALE - plusieurs centaines de messages pour un
seul geste, chacun avec `{vector_angle (degres), vector_length (0.01 a ~1)}`
- puis `CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP` (14008, message vide) au
relachement. Ce dernier n'avait AUCUN decodage dans le dispatcher (aurait
timeout a l'usage) - corrige.

Ajoute `perform_motor_joystick_v3(vector_angle, vector_length)` et
`perform_motor_joystick_stop_v3()`. Attention documentee dans le code :
`connect_socket()` est synchrone (attend une reponse a chaque appel), donc
pas adapte a reproduire un geste de glisser continu a haute frequence comme
le fait l'appli - correct pour un mouvement ponctuel (petit ajustement de
cadrage), pas pour un pilotage temps reel fluide.

## Balance des blancs : table complete des 7 presets confirmee

Table officielle fournie (source `data_dwarf3_config.ts`), et confirmee par
recoupement avec la sequence deja capturee precedemment (l'utilisateur avait
cycle mode=2 avec value=0,2,1,3 en parcourant les options a l'ecran dans
l'ordre "Incandescent, Fluorescent, Warm Fluorescent, Sunlight") :

```
index=0  Incandescent        index=4  Cloudy
index=1  Warm Fluorescent    index=5  Shadow
index=2  Fluorescent         index=6  Twilight
index=3  Sunlight
```

Verifie par calcul : parcourir "Incandescent, Fluorescent, Warm Fluorescent,
Sunlight" (ordre d'AFFICHAGE dans l'appli) donne exactement les valeurs
brutes 0, 2, 1, 3 - identique a la sequence deja capturee. Confirme aussi
que l'ordre d'AFFICHAGE de l'interface (Incandescent, Fluorescent, Warm
Fluorescent, Sunlight, Cloudy, Twilight, Shadow) est different de l'ordre
des index du protocole (0 a 6 ci-dessus) - seul l'index/valeur brute compte
pour piloter l'appareil, l'ordre visuel de l'appli n'a pas besoin d'etre
reproduit.

Ajoute : `AllowedWBPreset` (data_utils.py), `get_wb_preset_index_by_name()`,
et `perform_set_wb_preset_by_name_v3(name)` (dwarf_utils.py) - fixe
automatiquement `mode=2` (confirme = mode preset). La balance des blancs
est donc maintenant entierement couverte : mode Kelvin manuel
(`perform_set_wb_v3()` + table `AllowedWBTemp`) et mode preset
(`perform_set_wb_preset_by_name_v3()` + table `AllowedWBPreset`).

## Ajoute : perform_read_all_camera_params_v3() - lecture groupee

Vous avez remarque a raison qu'il n'existait pas d'equivalent V3 de
l'ancien `perform_get_all_camera_setting()` (V2) qui rassemble tous les
parametres en un seul appel. Ajoute :

```python
perform_read_all_camera_params_v3(dwarf_id="2")
```

Retourne un dict avec `exposure`, `gain`, `wb`, `brightness`, `contrast`,
`saturation`, `hue`, `sharpness`, `burst_count`, `burst_interval`,
`timelapse_interval`, `timelapse_duration`. Chaque champ vaut `None` si la
valeur correspondante n'a pas encore ete recue depuis la connexion (rappel :
V3 n'a pas de requete GET active, voir plus haut - c'est une lecture du
cache alimente passivement par les notifications `CMD_NOTIFY_GENERAL_INT_PARAM`).

Ne couvre pour l'instant que les parametres "photo tele" confirmes ; pas
encore les equivalents wide, ni les parametres specifiques a l'astro.

Verifie par simulation (cache rempli avec les valeurs exactes de vos
captures precedentes) : reproduit fidelement exposition=0.5/gain=50/
WB=Fluorescent/luminosite=58/etc.

## A tester : CMD_CAMERA_TELE_GET_ALL_PARAMS (V2) recoit-elle une reponse en V3 ?

Point de clarification : jusqu'ici, on a seulement observe que l'appli
officielle N'ENVOIE JAMAIS cette commande (10036) dans les captures reseau
analysees - ca ne prouve PAS que le firmware ne repondrait pas si on
l'envoyait nous-memes. Ce n'a encore jamais ete teste activement.

Ajoute `test_get_all_params_v2.py` : envoie explicitement
`CMD_CAMERA_TELE_GET_ALL_PARAMS` (via `perform_get_all_camera_setting()`,
message inchange, dispatcher deja capable de decoder la reponse - heritage
V2 jamais retire) dans deux scenarios (sans mode actif, puis apres
`perform_enter_photo_mode()`), pour trancher empiriquement.

Attention : si le firmware ne repond effectivement pas, le script patiente
jusqu'au timeout habituel (~30s) dans chaque scenario avant de conclure a
l'echec - comportement normal, pas un bug.

**Confirme sur materiel reel** : timeout (150s, delai maximal configure)
dans les DEUX scenarios (sans mode actif, et apres `perform_enter_photo_mode()`).
Le firmware V3 ne repond effectivement plus a `CMD_CAMERA_TELE_GET_ALL_PARAMS`,
meme envoyee explicitement en dehors de tout usage par l'appli officielle -
ce n'etait donc pas juste un choix de l'appli, la commande est bien
abandonnee cote firmware. Confirme definitivement que le mecanisme de
lecture des parametres en V3 passe exclusivement par les notifications
passives `CMD_NOTIFY_GENERAL_INT_PARAM` (voir `perform_read_all_camera_params_v3()`
plus haut) - il n'existe pas d'alternative "GET" active, ni V2 ni V3.

## Correction importante : mode=8 n'est PAS "astro generique", c'est le mode Soleil

En explorant la documentation de `dwarfAlp` (`docs/firmware/10-astronomy-functions.md`,
extraite directement du firmware, marquee VERIFIED), la table complete des
modes de prise de vue a ete trouvee :

| ID | Mode | Techniques |
|---|---|---|
| 1 | Normal | photo, burst, video, timelapse |
| 2 | **DSO** (Deep Sky Object) | stacking |
| 3 | Sun/Moon (parent) | stacking, burst, video, timelapse |
| 4 | Milky Way | stacking, timelapse |
| 5 | Star Trail | stacking |
| 8 | **Sun** | stacking, burst, video, timelapse |
| 9 | **Moon** | stacking, burst, video, timelapse |
| 10 | **Planet** | stacking, burst, video, timelapse |

**Tout notre code utilise `mode=8` pour "astro"** (`SHOOTING_MODE_ASTRO = 8`
dans `dwarf_utils.py`), convention reprise de `dwarfAlp` qui l'utilise pour
son propre cas d'usage. Mais d'apres cette table, **mode=8 est
specifiquement le mode Soleil**, pas un mode astro generique. Le mode
generique pour le ciel profond (galaxies, nebuleuses, amas...) est
`mode=2` (DSO).

Ca n'invalide pas nos tests actuels (mode=8 a bien fonctionne comme mode
stacking/astro dans tout ce qu'on a teste), mais **c'est a reconsiderer
avant d'attaquer le GOTO + stacking** : pour du ciel profond classique,
utiliser `mode=2` (DSO) plutot que `mode=8`. Reserver 8/9/10
(Soleil/Lune/Planete) aux cibles specifiques correspondantes, qui ont
vraisemblablement un comportement de suivi/tracking adapte a ces objets
(mouvement rapide pour la Lune/les planetes, filtre solaire pour le Soleil).

Note complementaire (meme document, `08-camera-system.md`) : "DSO tele
defaults are 15 seconds and gain 60" et gain defini sur une plage 0-120
(pas 0-240 comme dans les tables `AllowedGains`/`AllowedGainsD3` V2/D3) -
peut-etre une plage differente propre a la Mini ou au mode DSO
specifiquement, a verifier.



## API HTTP live (port 8082) : shootingMode/getParamAndSetting

Vous avez rappele que `getDefaultParamsConfig` (V2, port 8082) ne donne plus
grand-chose en V3, et mentionne un nouvel endpoint POST
`/shootingMode/getParamAndSetting` cote appli (ALP) sans arriver a obtenir
de resultat live. En creusant la documentation de `dwarfAlp`
(`docs/apk-analysis/capture-workflows.md`, analyse de l'APK officiel +
tests reels), l'endpoint est bien documente et confirme fonctionnel :

```
POST http://<ip>:8082/shootingMode/getParamAndSetting
Body JSON : {"modeId": <id>}
```

**Confirmation independante forte** : dwarfAlp rapporte, pour `modeId=2`
(DSO/astro) sur une Dwarf Mini reelle, `exposure param_id=144396663052566529`
et `gain param_id=144396663052566530`. Convertis en hexadecimal :
`0x0201000000000001` et `0x0201000000000002` - **exactement**
`PARAM_ID_ASTRO_EXPOSURE`/`PARAM_ID_ASTRO_GAIN` deja utilises dans ce repo
(recuperes plus tot directement du code source de dwarfAlp). Confirmation
croisee complete, aucune divergence.

Cet endpoint est very probablement le moyen le plus fiable de retrouver
TOUS les param_id sans deviner par capture reseau - notamment ceux qu'on
n'a identifies jusqu'ici que par capture reseau pour le mode Normal/photo
(luminosite, contraste, saturation, teinte, nettete, burst, timelapse).

**Piste pour expliquer "pas de resultat live"** : d'apres le workflow
documente par dwarfAlp, l'appli officielle appelle cet endpoint APRES avoir
deja etabli une session WebSocket active (MASTER LOCK, entree en mode via
`ENTER_CAMERA`...), pas a froid des la connexion. Le firmware pourrait tres
bien ignorer/vider sa reponse si aucune session WS n'est active en
parallele.

**Ajoute** : `perform_get_default_params_config_http()` et
`perform_get_param_and_setting_http(mode_id)` (HTTP simple via `requests`,
independant du protocole WebSocket/protobuf), plus `test_get_param_and_setting_http.py`
qui etablit d'abord une session WS (mode photo puis mode astro) avant
d'essayer les deux appels HTTP, pour verifier l'hypothese ci-dessus.

## Recette complete du GOTO + stacking astro (bonus, pour la prochaine etape)

En lisant `docs/apk-analysis/capture-workflows.md` de `dwarfAlp` en detail,
la sequence complete utilisee par l'appli officielle pour une capture
Deep Sky (Dwarf 2/3/Mini) est documentee avec un piege d'ordonnancement
important a retenir pour la prochaine etape (GOTO + stacking) :

```
POST shootingMode/getParamAndSetting {modeId:2}   -> catalogue live
16700  exposure param (manuel, index exact du firmware)
16701  gain param (manuel)
11041  ReqSetQuickSet (tuple quick-set persiste - PAS un setter generique)
16703  nombre de frames absolu
11005  ReqCaptureRawLiveStacking(ir_index=1 ou 2)
   -> 15264 (espace de noms de parametres actif, module 15)
16700/16701/16703 reappliques dans cet espace de noms actif
   -> notifications d'etat/progression de capture
11006  quand 15209.current_count atteint le nombre de frames demande
   -> 15208 (arret en cours = 2, puis arrete = 3)
```

**Piege documente** : envoyer 11041 AVANT 16700 fait que le firmware
actuel rejette 16700 avec le code -1. L'ordre qui fonctionne est
16700/16701, puis 11041, puis 16703. Cet ordre "prime" aussi la Dwarf 3
avant 11005. La notification 15288 rapporte la duree d'exposition
effectivement choisie par le firmware (peut differer de la demande).

A garder sous le coude pour l'implementation du GOTO + stacking.

## API HTTP live confirmee fonctionnelle - reponse complete modeId=1 (Normal/photo)

Vous avez teste avec succes `POST /shootingMode/getParamAndSetting {"modeId":1}`
apres avoir etabli une session WS (confirme : il fallait bien une session
active, comme suppose). La reponse est extremement riche et confirme/etend
tout ce qu'on avait reconstruit par capture reseau.

### Confirmation totale des valeurs deja capturees

`currentValue` dans la reponse live correspond EXACTEMENT a ce qu'on avait
capture manuellement au meme instant : exposition tele=111 ("0.5"), gain
tele=50, burst count=5, burst interval=20, timelapse interval=4, timelapse
total time=120 ("2 min"). Aucune divergence.

### Note sur le champ "paramId" de cette API HTTP

Pour `generalParams` (brightness/contrast/saturation/hue/sharpness) et pour
`exp`/`gain`/`wb`, l'API HTTP renvoie le MEME `paramId` pour tous les champs
d'un meme groupe (probablement un artefact de serialisation cote appli -
elle semble reutiliser le dernier param_id du groupe plutot que le vrai
param_id individuel de chaque champ). **Les vrais param_id individuels,
confirmes par capture reseau directe du protocole WebSocket, restent ceux
deja utilises dans ce repo** (`PARAM_ID_PHOTO_TELE_BRIGHTNESS` = ...04,
`_CONTRAST` = ...05, etc.) - l'ordre des champs dans le JSON (brightness,
contrast, saturation, hue, sharpness) confirme neanmoins parfaitement notre
mapping deja etabli.

### Nouveau : plage d'exposition etendue jusqu'a 180 secondes

La reponse live revele un palier au-dela de ce qu'on avait meme dans la
table D3 la plus complete : `index=168, name="180"` (3 minutes). Ajoute a
`AllowedExposuresD3` dans `data_utils.py`.

Egalement revele : des plages MIN/MAX differentes SELON LA TECHNIQUE
(`techId` 1=photo, 3=burst, 4=video, 5=timelapse) - ex. le video (techId=4)
est plafonne a `maxValue=111` (~0.5s), alors que photo/burst/timelapse
autorisent jusqu'a 168 (180s). Logique (une video ne peut pas avoir une
"exposition" de plusieurs minutes par frame) mais pas encore exploite dans
le code - a garder en tete si vous voulez valider les bornes avant
d'envoyer une valeur.

### Nouveau : table de gain GRAND ANGLE (wide) totalement differente

Le tele et le grand angle (wide) ont des plages de gain completement
differentes - jamais capture jusqu'ici (on n'avait teste que le tele) :

- **Tele** : 0-240, valeurs `[0,2,5,10,20,30,...,240]` (correspond a la
  table `AllowedGainsD3` deja presente, confirmee applicable au tele Mini).
- **Grand angle** : **0-2500** (!), valeurs
  `[40,50,60,...,700,1000,1300,1600,1900,2200,2500]` - plage bien plus
  large avec des paliers irreguliers en haut de plage. Nouvelle table
  `AllowedGainsWide` ajoutee dans `data_utils.py`, avec
  `get_wide_gain_v3_index_by_name()` (attention : ici "index" retourne
  directement la valeur numerique, pas un index de table au sens des
  autres fonctions de ce fichier - l'API live ne fournit qu'une liste
  plate pour ce champ).

### Nouveau : semantique complete des 3 modes de balance des blancs

```
"wb": { "currentMode": 0, "currentValue": 5542, "modes": [0, 1, 2],
        "ctModeValues": [2800...7500],       <- mode 0 : Kelvin manuel
        "sceneModeValues": [0,1,2,3,4,5,6],  <- mode 2 : preset (AllowedWBPreset)
        "sceneValue": 0, "defaultScene": 3 }
```

Confirme : `mode=0` = Kelvin manuel (`currentValue` = temperature K brute,
ici 5542K), `mode=2` = preset/scene (le `sceneValue` distinct du
`currentValue` - a noter, structure legerement plus riche que ce qu'on
avait suppose : deux champs separes plutot qu'un seul `value` reinterprete
selon le mode). `mode=1` reste a elucider (probablement "Auto") - pas
encore observe dans une capture reseau.

### Nouveau : contraintes du burst confirmees + reglages appareil decouverts

`burstCount` : `min=3, max=1000` (impossible de descendre sous 3 photos).
Toutes les valeurs valides de burst interval/timelapse interval/timelapse
total time confirmees EXACTEMENT identiques a nos tables deja portees
(`AllowedBurstInterval`, `AllowedTimelapseInterval`,
`AllowedTimelapseTotalTime`), y compris la liste complete en secondes pour
`timelapseTotalTime` : `[0,120,300,480,600,1200,1800,2400,3000,3600,7200,
10800,14400,18000]` (0=illimite, confirme).

`deviceParams` : 3 reglages au niveau appareil decouverts (non testes en
ecriture) : `autoShutdown` (bool), `wideMatchingFrameCalibration` (bool),
`disableHostSlave` (bool, defaultValue=true !). Ce dernier est
particulierement interessant : si le mecanisme MASTER/SLAVE est DESACTIVE
PAR DEFAUT sur cet appareil, ca expliquerait completement pourquoi
`set_HostMaster()` ne recoit jamais de reponse (voir plus haut, "MASTER
LOCK : probablement vestigial") - meme si `currentValue` rapporte `false`
au moment de cette capture precise (peut-etre modifie entre-temps, ou
signification inversee du nom). Constantes ajoutees
(`PARAM_ID_DEVICE_AUTO_SHUTDOWN` etc.) mais pas encore de fonction de
lecture/ecriture dediee - a faire si vous voulez exploiter ces reglages.

### A faire si vous avez aussi le resultat pour modeId=2 (DSO/astro)

Si vous avez recupere la reponse pour `modeId=2`, envoyez-la egalement :
ca devrait confirmer les param_id astro (`PARAM_ID_ASTRO_EXPOSURE`/`GAIN`,
deja confirmes independamment par la documentation dwarfAlp) et reveler
d'eventuels parametres specifiques a l'astro (binning, format FITS,
nombre de sous-poses cible, etc.) qu'on n'a pas encore explores.

## Reponse live modeId=2 (DSO/astro) - directement exploitable pour le GOTO + stacking

### Confirmation totale

`exp`/`gain` tele : `currentValue=111`/`50` - identique a ce qu'on avait
deja. `paramId=144396663052566530` = `0x0201000000000002` = exactement
`PARAM_ID_ASTRO_GAIN` deja en place (meme "artefact de partage" du champ
paramId deja repere pour le mode photo - l'exposition ET le gain rapportent
le meme paramId, seul le vrai param_id individuel confirme par capture
WS compte).

### Nouveau : reglages du nombre de sous-poses (directement utile pour le stacking)

`shootingTechSettings` (cameraId=0/tele et cameraId=1/wide) revele :

```
stackCount (tele)   : 1-999, valeur observee 390    -> PARAM_ID_ASTRO_STACK_COUNT_TELE
stackCount (wide)   : 1-999, valeur observee 100    -> PARAM_ID_ASTRO_STACK_COUNT_WIDE
mosaicCount (tele)  : 1-249, valeur observee 45     -> PARAM_ID_ASTRO_MOSAIC_COUNT_TELE
```

Ajoute `perform_set_astro_stack_count_v3(count, camera="tele"|"wide")` et
`perform_set_astro_mosaic_count_v3(count)`.

### Nouveau : calibration automatique (bool)

`shootingModeParams.autoCalibration` (specifique au mode, pas a la camera) :
`defaultValue=true`, `currentValue=false` au moment de la capture (rejoint
la remarque deja notee de la doc dwarfAlp : "auto_calibration defaults true
for DSO..."). `PARAM_ID_ASTRO_AUTO_CALIBRATION = 0x0203f00000000064`.

Necessite un type de message different (`ReqSetGeneralBoolParams`, pas
`ReqSetGeneralIntParam`) et donc probablement une commande differente.
`CMD_PARAM_SET_GENERAL_BOOL_PARAMS = 16705` **non confirme par capture
reseau directe** - infere par la meme methode (position sequentielle dans
`param.proto`) qui avait deja correctement identifie `CMD_PARAM_SET_WB=16702`.
Ajoute `perform_set_bool_param_v3()` et
`perform_set_astro_auto_calibration_v3(enabled)`, avec decodage de reponse
ajoute au dispatcher par precaution - **a verifier par capture reseau si
vous le testez**.

### Contrainte importante decouverte : gain minimum different en astro

`"range": [{"maxValue": 240, "minValue": 40, "techId": 2}]` pour le gain
tele en astro - **minimum 40, pas 0** (contrairement au mode photo normal
ou le gain peut descendre a 0). A garder en tete avant d'envoyer une valeur
de gain trop basse en astro.

### filterType en astro : VIS indisponible

`filterType` : `values=[1,2]` seulement en mode astro (contre `[0,1,2]`
generalement) - le filtre VIS (0, "normal") n'est logiquement pas propose
en mode DSO, seuls Astro(1)/Duo-Band(2) le sont.

### NON FIABLE : param_id astro cote camera grand angle (wide)

Les `paramId` rapportes pour `exp`/`gain` (wide) et `stackFormat` ont un
motif d'octets incoherent avec le reste (ex. `02 01 0f ff ff ff ff fc` au
lieu du motif attendu `02 01 1x...`) - tres probablement un artefact de
calcul cote appli pour la camera wide (division/offset qui deborde). **Ne
pas utiliser ces valeurs sans confirmation par capture reseau directe** si
vous faites de l'astro sur la camera grand angle.

### Bonus : reglages generiques mode astro (stackFormat, displaySource, stackBinning)

`shootingTechSettings` (cameraId=15, virtuel) revele aussi `stackFormat`
(`values=[2,3]`, probablement FITS/TIFF - correlé avec la doc dwarfAlp qui
mentionne ces deux formats), `displaySource` (`[0,1]`) et `stackBinning`
(`[0,1]`) - pas encore implementes (paramId de stackFormat dans le lot
"non fiable" ci-dessus, displaySource/stackBinning a verifier egalement
avant utilisation).

## Ajoute : perform_read_camera_params_http_v3() - "GET all params" fiable via HTTP

Vous avez fait remarquer, a raison, que le champ `currentValue` de l'API
HTTP donne acces aux valeurs COURANTES reelles - ce qui en fait une bien
meilleure source que le cache de notifications passives
(`perform_read_all_camera_params_v3()`, base sur `CMD_NOTIFY_GENERAL_INT_PARAM`) :

- **Requete active** : renvoie toujours l'etat courant reel, pas de risque
  de `None` si aucune notification n'est encore arrivee.
- **Couvre bien plus de parametres** : filtre, resolution, framerate,
  nombre de sous-poses, calibration auto... en plus de exposition/gain/WB/
  luminosite/contraste/saturation/teinte/nettete/burst/timelapse.
- **Les deux cameras** (tele ET wide) en un seul appel, avec des valeurs
  distinctes et coherentes pour chacune.

Ajoute `perform_read_camera_params_http_v3(mode_id)` : appelle
`perform_get_param_and_setting_http()` et transforme le JSON brut en un
dict propre et lisible :

```python
{
    "mode_id": 1,
    "cameras": {
        0: {"brightness": 58, "contrast": 52, ..., "filterType": 1,
            "exposure": {"mode": 1, "value": 111, "name": "0.5"},
            "gain": {"mode": 1, "value": 50},
            "wb": {"mode": 0, "value": 5542, "scene": 0}},
        1: { ... },  # wide, memes cles
    },
    "device": {"autoShutdown": True, "disableHostSlave": False, ...},
    "shooting_mode": {"autoCalibration": False, ...},   # si fourni par le mode
    "tech_settings": {15: {...}, 0: {"stackCount": 390, ...}, 1: {...}},
}
```

Verifie par reconstruction exacte de votre reponse `modeId=1` reelle :
reproduit fidelement toutes les valeurs (luminosite=0, nettete=30,
exposition=111/"0.5", gain=50, WB=5542K, burst=5/20s, timelapse=4s/120s).

`test_get_param_and_setting_http.py` mis a jour pour afficher a la fois la
reponse brute et ce resume lisible, pour `modeId=1` et `modeId=2`.

**A privilegier desormais** pour la lecture de l'etat courant plutot que
`perform_read_all_camera_params_v3()` (qui reste utile en complement pour
un suivi en temps reel via notifications, sans avoir a repeter une requete
HTTP).

## Script de collecte multi-appareils : dump_device_info.py

Puisque vous avez aussi un Dwarf 3 et un Dwarf 2 en plus de la Mini, ajoute
`dump_device_info.py` : collecte systematiquement toutes les infos possibles
(MASTER LOCK, heure/fuseau, GET_DEVICE_STATE_INFO, getDefaultParamsConfig,
puis getParamAndSetting live pour chaque mode 1/2/3/4/5/8/9/10) et ecrit un
rapport JSON horodate (`device_report_<label>_<horodatage>.json`).

**Tolerant aux echecs par construction** : on ne sait pas si le Dwarf 2
(materiel plus ancien) supporte meme le protocole V3 - chaque etape est
executee independamment (`safe_call()`), une exception ou un echec sur
l'une n'empeche pas les suivantes de s'executer, et tout est consigne
(succes ou echec, avec le detail de l'erreur) dans le rapport final. Meme
un Dwarf 2 qui echoue partout produira un rapport exploitable montrant
precisement a quel point le protocole V3 (ou pas) y fonctionne.

Usage :
```
python dump_device_info.py --label mini
python dump_device_info.py --label dwarf3
python dump_device_info.py --label dwarf2
```

Envoyez-moi les 2-3 rapports JSON obtenus : je pourrai les comparer
directement (param_id, plages de valeurs, modes/techniques supportes) pour
identifier precisement ce qui differe entre les trois modeles.

## Comparaison Mini / Dwarf 3 / Dwarf 2 : premiers resultats tres instructifs

Merci pour les 3 rapports (`dump_device_info.py`). Deux decouvertes
importantes, plus un vrai bug corrige.

### Bug corrige : crash sur les modes non supportes par un appareil

`perform_read_camera_params_http_v3()` plantait (`TypeError: 'NoneType'
object is not iterable`) sur Dwarf 2, modes 4 et 5 (Milky Way, Star Trail -
que le Dwarf 2 ne supporte pas). Cause : `.get(cle, defaut)` ne renvoie
`defaut` QUE si la cle est ABSENTE - or le firmware renvoie explicitement
`"cameraParams": null` (et autres champs `null`) pour un mode non
supporte, ce qui faisait planter `for cam in None:`. Corrige (toutes les
lectures utilisent desormais `(valeur or defaut)` plutot que
`.get(cle, defaut)` seul) et verifie par reproduction exacte du cas Dwarf 2.

### Bonne nouvelle : le protocole V3 est bien commun aux 3 appareils

Les 3 rapports affichent `majorVersion=2, minorVersion=6` pour la version
d'API/protocole (distincte de la version de firmware propre a chaque
modele) - **confirme que ce n'est pas une specificite Mini**, toute la
gamme (Dwarf 2, Dwarf 3, Mini) parle bien ce protocole V3.

### MASTER LOCK echoue identiquement sur les 3 appareils

Confirme de maniere definitive que ce n'est PAS une particularite de la
Mini : `set_HostMaster()` echoue exactement pareil sur Dwarf 2 et Dwarf 3.
Le mecanisme MASTER/SLAVE semble donc bien abandonne/non-repondant sur
toute la gamme en V3, pas seulement sur le materiel recent.

### getDefaultParamsConfig confirme "identification seule" sur toute la gamme

Les 3 appareils renvoient leur nom/version de firmware correctement
(`DWARF MINI` id=4 fw=1.1.3, `DWARF3` id=2 fw=1.5.2, `DWARF II` id=1
fw=2.2.18) mais `cameras: []` et `featureParams: []` partout - confirme
que cet endpoint legacy ne sert plus que pour l'identification de
l'appareil, plus pour le catalogue de parametres, sur toute la gamme.

### Modes supportes : repartition tres differente entre appareils

```
          mode: 1    2    3    4    5    8    9    10
Mini    :      OK   OK   OK   OK   OK   OK   OK   OK
Dwarf 2 :      OK   OK   OK   --   --   OK   OK   OK    (4,5 non supportes, reponse null propre)
Dwarf 3 :      --   --   --   OK   OK   --   --   --    (echec HTTP sur 1,2,3,8,9,10)
```

- **Mini** : le plus complet, tous les modes fonctionnent.
- **Dwarf 2** : ne supporte pas Milky Way (4) ni Star Trail (5) - reponse
  propre (`null`), pas un bug reseau, juste une capacite absente sur ce
  modele. Coherent avec un capteur/optique plus ancien.
- **Dwarf 3** : motif INVERSE et suspect - seuls Milky Way (4) et Star
  Trail (5) reussissent, les 6 autres modes (dont DSO=2, le mode astro
  standard !) echouent avec "returned False" (erreur HTTP, pas une reponse
  `null` propre comme sur le Dwarf 2). Ce n'est probablement PAS une
  vraie limitation materielle (DSO existe forcement sur un Dwarf 3) mais
  plutot un probleme de timing ou de parametre d'entree (le `tech=2`
  utilise par defaut dans le script n'est peut-etre pas valide pour ces
  modes sur Dwarf 3 specifiquement, ou l'appareil a besoin de plus de
  delai apres le changement de mode avant de repondre a l'API HTTP).

**Correctif applique dans `dump_device_info.py`** : delai augmente (1s ->
2s) avant l'appel HTTP, et une seconde tentative automatique apres 3s
supplementaires en cas d'echec - a re-tester sur le Dwarf 3 pour voir si
c'etait bien un probleme de timing. Le detail exact de l'erreur HTTP
(code, message) n'est pour l'instant visible que dans les logs console
(pas dans le JSON) - si le probleme persiste, partagez la sortie console
complete du Dwarf 3 pour ce point precis, elle contient le vrai message
d'erreur derriere le "returned False".

### Autres differences notees en passant

- Balance des blancs : Dwarf 2 rapporte `scene: -1` (Mini/Dwarf3 utilisent
  0 par defaut) - sentinelle "aucune scene selectionnee" probablement
  specifique au Dwarf 2.
- `stackCount` (tele astro) : Dwarf 2 monte a 999 (mosaicCount=50, proche
  des 45 observes sur Mini), coherent avec la meme famille de reglages.

## Dwarf 3 : le delai a partiellement resolu le probleme, hypothese de "chauffe" confirmee

Nouveau rapport apres le premier correctif (delai 1s->2s + une nouvelle
tentative) : les modes 8, 9, 10 reussissent desormais (echouaient avant),
seuls 1, 2, 3 echouent encore - **exactement les 3 premiers modes testes
dans la boucle**. Ca ecarte l'hypothese "certains modes echouent
specifiquement" au profit d'une **periode de stabilisation du firmware
juste apres la connexion**, independante du mode teste.

Confirme par votre capture manuelle du mode 2 (probablement effectuee plus
tard, laissant plus de temps au firmware pour se stabiliser) : reponse
complete et valide obtenue pour `modeId=2` sur Dwarf 3.

**Bonus de cette capture** : tous les `param_id` (exposition/gain tele,
stackCount, mosaicCount, autoCalibration) sont **exactement identiques**
a ceux de la Mini - confirme que l'implementation est bien portable sur
toute la gamme, pas specifique a un modele.

**Corrige dans `dump_device_info.py`** :
- Delai de "chauffe" de 8 secondes ajoute juste apres la connexion, avant
  de commencer les tests par mode.
- Repasse finale automatique sur tous les modes en echec, une fois tous
  les autres testes (resultat stocke dans `retry_at_end` pour chaque mode
  concerne) - preuve directe, dans le meme rapport, si l'hypothese de
  chauffe est la bonne cause.

Valeurs de reference notees pour Dwarf 3 (astro/DSO, camera tele) :
exposition max=165 ("120", legerement moins que les 168 ("180") de la
Mini), gain 40-240 (tele) / 0-240 (wide, plus restreint que le potentiel
0-2500 de la Mini en mode photo - a confirmer si le wide grand angle du
Dwarf 3 a la meme plage etendue que la Mini en photo simple), stackCount
tele max=999 (courant 330), mosaicCount max=249 (courant 63).

## Confirme : le delai de "chauffe" de 8s resout completement le probleme Dwarf 3

Nouveau rapport apres ajout du delai initial : les 8 modes (1,2,3,4,5,8,9,10)
reussissent tous des le premier passage - plus besoin de la repasse finale.
Hypothese de periode de stabilisation firmware **confirmee** comme la cause
racine du probleme initial, pas une limitation par mode.

**A retenir pour toute utilisation de l'API HTTP live** (`shootingMode/getParamAndSetting`) :
prevoir un delai de quelques secondes (8s empiriquement suffisant sur
Dwarf 3, potentiellement variable selon le modele/l'etat de l'appareil)
apres l'etablissement de la session WS (MASTER LOCK, entree en camera)
avant le premier appel HTTP - sans quoi les premieres requetes peuvent
echouer meme si les suivantes fonctionnent parfaitement.

## Correctif : connect_bluetooth_cmd.py supposait a tort un retour dict

Vous avez corrige `connect_ble_direct_dwarf()` pour qu'elle renvoie un
simple `bool` plutot qu'un dict `{is_connected, ip_address, error}`.
`connect_bluetooth_cmd.py` (mon script `--cmd`) supposait encore l'ancien
format et aurait plante des `result.get(...)` sur un bool. Mis a jour pour
utiliser directement `if result:` / `else:` - l'IP est de toute facon deja
ecrite dans `config.ini` par la fonction elle-meme en cas de succes.

## main_v3.py : adaptation du menu interactif de dwarf_test_apiV2

Nouveau `main_v3.py` : reprend le squelette du menu texte interactif de
`dwarf_test_apiV2/main.py` (menu principal + sous-menus + boucle), mais
entierement cable sur les fonctions V3 verifiees construites tout au long
de ce projet.

**Focus sur la camera** (18 options, C1 a C18) comme demande :
- C1/C2 : entree en mode Photo simple / Astro-DSO
- C3 : lecture groupee des parametres actuels (API HTTP live)
- C4-C9 : reglages exposition/gain/balance des blancs (Kelvin et preset)/
  luminosite-contraste-saturation-teinte-nettete/filtre IR
- C10/C11 : reglages burst (nombre + intervalle) et timelapse (intervalle +
  duree)
- C12-C15 : prise de photo simple, demarrage/arret rafale/video/timelapse
- C16 : autofocus
- C17/C18 : reglages astro (stackCount/mosaicCount, calibration automatique)

Plus un sous-menu Moteur (mouvement ponctuel au joystick) et les fonctions
generales deja solides (connexion complete, diagnostic, statut,
deconnexion, reboot, extinction).

**Fonctions manquantes ajoutees au passage** : en construisant ce menu, il
manquait encore les fonctions de DECLENCHEMENT du burst/video/timelapse
elles-memes (on n'avait code que les reglages et le decodage des
notifications de fin) - ajoute `perform_start_burst_v3()`/`perform_stop_burst_v3()`,
`perform_start_record_v3()`/`perform_stop_record_v3()`,
`perform_start_timelapse_v3()`/`perform_stop_timelapse_v3()` (module
CAMERA_TELE, commandes V2 inchangees 10003/10004/10005/10006/10033/10034).
Decodage des 3 commandes STOP ajoute au dispatcher au passage (n'existait
pas encore, meme piege que d'habitude si on avait laisse tel quel).

**Ce qui n'est PAS encore dans ce menu** : le GOTO + stacking astro complet
(prochaine etape du projet - seule l'entree en mode et les reglages
stackCount/calibration sont disponibles ici, pas le declenchement du
stacking lui-meme ni le pointage).

Teste : compilation, import, et simulation de navigation dans le menu
(entree C1 -> verification que `perform_enter_photo_mode()` est bien
appelee) - fonctionne correctement de bout en bout au niveau logique. Pas
teste contre du materiel reel (necessite une connexion active).

Usage :
```
python connect_bluetooth_cmd.py --ssid "..." --pwd "..."   # une fois
python main_v3.py
```

## main_v3.py : sous-menu Bluetooth ajoute

Ajoute au menu principal (option `B`) et un sous-menu dedie, sur le meme
modele que `dwarf_test_apiV2/main.py` :

- **B1** : connexion Bluetooth directe (ligne de commande, `bleak`) -
  reutilise `connect_ble_direct_dwarf()`.
- **B2** : connexion Bluetooth via navigateur web - reutilise
  `connect_bluetooth()`.
- **B3** : affiche la configuration Bluetooth sauvegardee (`config.ini`).
- **B4** : modifie SSID/mot de passe WiFi et mot de passe Bluetooth
  (version simplifiee par rapport a `input_bluetooth_data()` de la V2, qui
  couvre aussi des champs plus rarement utilises comme le type WiFi AP/
  demarrage automatique/pays - ceux-ci restent lisibles via B3 mais pas
  modifiables depuis ce menu pour l'instant).

Apres une connexion reussie (B1 ou B2), la sequence V3 complete
(MASTER LOCK + heure/fuseau, meme logique que l'option 1 du menu principal)
est enchainee automatiquement.

Teste (logique de dispatch, avec les imports Bluetooth/tkinter/bleak-winrt
stubbes puisqu'ils dependent de l'environnement - tkinter et le backend
winrt de `bleak` ne sont disponibles que sous Windows, cohérent avec votre
environnement) :
- B1 : verifie que `connect_ble_direct_dwarf()` puis `option_1()` sont bien
  appeles en cas de succes.
- B4 : verifie que la sauvegarde dans `config.ini` fonctionne correctement
  (SSID et mot de passe bien ecrits).

## Module Astro (autofocus, EQ, calibration, exposition/gain/stackCount, suivi du stacking)

Bonne nouvelle constatee en creusant ce point : la quasi-totalite de
l'infrastructure necessaire existait deja cote V2 (`perform_calibration`/
`perform_stop_calibration`, `perform_start_autofocus(infinite=)`/
`perform_stop_autofocus`, `start_polar_align`/`stop_polar_align` pour l'EQ,
`perform_takeAstroPhoto`/`perform_stopAstroPhoto`, `perform_goto`/
`perform_goto_stellar`/`perform_stop_goto`), utilise des commandes/messages
confirmes inchanges en V3, ET le dispatcher les gere deja correctement
grace aux renommages de `notify.proto` deja effectues plus tot dans ce
projet (`OperationStateNotify`, `ProgressCaptureRawLiveStacking` avec le
bon champ `update_type`, `AstroCalibrationState`, `EqSolvingState`).

Verifie systematiquement (script de controle re-execute) : aucune classe
protobuf utilisee dans le dispatcher n'est manquante, toutes les paires
`VALID_PAIRS` necessaires (calibration, autofocus astro, EQ, stacking
start/stop/progress) sont deja presentes.

**Ajoute** (ce qui manquait reellement) :
- `perform_set_astro_exposure_v3()`/`perform_set_astro_exposure_by_name_v3()`
  et `perform_set_astro_gain_v3()` - reutilisent les fonctions generiques
  deja existantes (`perform_set_exposure_v3`/`perform_set_gain_v3`) avec
  `PARAM_ID_ASTRO_EXPOSURE`/`PARAM_ID_ASTRO_GAIN` (confirmes identiques
  entre Mini et Dwarf 3, et confirmes independamment par dwarfAlp).
- `perform_read_astro_stacking_status_v3()` - lit l'etat de la session de
  stacking (`capturing`, `current_count`, `stacked_count`) depuis le cache
  deja alimente par le dispatcher (`get_client_status()`), sans requete
  reseau. Bug corrige en cours de route : `get_client_status()` renvoie
  `{"fullStatus": {...}, ...}`, pas directement le dict a plat - premiere
  version de la fonction lisait au mauvais niveau, corrige et verifie par
  simulation.

**Nouveau sous-menu Astro dans `main_v3.py`** (A1 a A10) : exposition,
gain, stackCount/mosaicCount, calibration (demarrer/arreter), autofocus
(normal ou infini, demarrer/arreter), EQ solving/alignement polaire
(demarrer/arreter), GOTO (RA/Dec ou objet du systeme solaire), stop GOTO,
demarrer/arreter une session de stacking, et lecture du statut de
progression.

**A garder en tete** : le nom du parametre `camera="tele"/"wide"` sur
`perform_set_astro_exposure_v3()`/`perform_set_astro_gain_v3()` n'est pas
encore reellement exploite (seul "tele" est confirme fiable - voir la note
plus haut sur les param_id wide astro incoherents) - parametre present pour
coherence d'API future, pas encore fonctionnel pour "wide".

Teste : compilation de tous les fichiers modifies, verification exhaustive
des classes protobuf utilisees (aucune manquante), tests de regression sur
`perform_read_astro_stacking_status_v3()` (connecte et non connecte), et
simulation de navigation dans le nouveau sous-menu Astro (demarrage
stacking, autofocus infini, lecture de statut) - tout fonctionne
correctement au niveau logique.

## Precision : qu'est-ce qui a VRAIMENT change en astro par rapport a V2 ?

Question posee et verifiee precisement dans le code V2 d'origine
(dwarf_python_api/lib/dwarf_utils.py, avant migration) - le tableau complet :

**A change (nouveau mecanisme V3, module CAMERA_PARAMS/15)** :
- `perform_enter_astro_mode()` - nouveau handshake (deja documente plus haut).
- **Exposition/gain** : en V2, `perform_update_camera_setting("exposure"/"gain", ...)`
  utilisait le module CAMERA_TELE (1) avec `CMD_CAMERA_TELE_SET_EXP_MODE`
  (10007)/`CMD_CAMERA_TELE_SET_EXP` (10009)/`CMD_CAMERA_TELE_SET_GAIN` -
  **la meme mecanique que pour la photo normale**, aucune distinction
  photo/astro cote V2. En V3, module CAMERA_PARAMS (15) avec un systeme de
  `param_id`, et memes des `param_id` DIFFERENTS pour photo (`0x0101...`)
  et astro (`0x0201...`).
- **Nombre d'images a empiler (stackCount)** : en V2, `ReqSetFeatureParams`
  avec `param.id=1` ("Astro img_to_take"), module CAMERA_TELE,
  `CMD_CAMERA_TELE_SET_FEATURE_PARAMS`. En V3, mecanisme totalement
  different (module CAMERA_PARAMS, `PARAM_ID_ASTRO_STACK_COUNT_TELE`).
- **Calibration automatique (`autoCalibration`)** : aucun equivalent trouve
  dans le code V2 - semble etre un concept propre a V3.

**N'a PAS change (memes commandes qu'en V2)** :
- Calibration de la plateforme (`perform_calibration`/`perform_stop_calibration`,
  module ASTRO, 11000/11001).
- Autofocus astro y compris le focus infini
  (`perform_start_autofocus(infinite=)`/`perform_stop_autofocus`, module
  FOCUS, 15004/15005).
- EQ/alignement polaire (`start_polar_align`/`stop_polar_align`, module
  ASTRO, 11018/11019).
- GOTO (`perform_goto`/`perform_goto_stellar`/`perform_stop_goto`).
- Demarrage/arret de la session de stacking elle-meme
  (`perform_takeAstroPhoto`/`perform_stopAstroPhoto`, 11005/11006).
- Le suivi de progression (dispatcher deja fonctionnel, seul le nommage
  des classes `notify.proto` avait change - deja corrige dans ce projet).

**A noter en complement** : V2 avait aussi `ReqSetFeatureParams` avec
`param.id=0` ("Astro binning") et `param.id=2` ("Astro format") - non
encore portes en V3 dans ce repo (pas demandes explicitement jusqu'ici,
mecanisme probablement migre vers le meme module CAMERA_PARAMS que
stackCount/mosaicCount si besoin de les exposer plus tard).

## Nouveaux champs protobuf decouverts sur les messages GOTO/stacking

Question posee : "un champ target avait ete ajoute ?" - verification faite
precisement en comparant les .proto V2 (avant migration) et V3
(dwarfAlp) message par message.

**Reponse precise** : `target_name` n'est PAS nouveau (deja present dans
`ReqGotoDSO`/`ReqGotoSolarSystem` en V2). Mais la comparaison a revele
d'AUTRES champs genuinement nouveaux, non exploites jusqu'ici :

```
ReqGotoDSO (V2: ra, dec, target_name)
  + goto_only (bool)       <- NOUVEAU en V3
  + rotation (optional int32)  <- NOUVEAU en V3

ReqGotoSolarSystem (V2: index, lon, lat, target_name)
  + force_start (bool)     <- NOUVEAU en V3

ReqCaptureRawLiveStacking (V2: message COMPLETEMENT VIDE)
  + ir_index (int32)        <- NOUVEAU en V3
  + force_start (bool)      <- NOUVEAU en V3
```

**Hypotheses sur leur role** (non confirmees par capture reseau,
deduites du nom/type de champ et du workflow documente par dwarfAlp) :
- `goto_only` : pointer sans demarrer automatiquement le stacking apres -
  permettrait de separer "pointer" de "capturer".
- `rotation` : angle de rotation camera/cadrage a appliquer pendant le GOTO.
- `force_start` (GotoSolarSystem) : forcer le GOTO malgre un avertissement
  recuperable (ex: cible proche/sous l'horizon) - meme motif que pour le
  stacking.
- `ir_index` (CaptureRawLiveStacking) : filtre a utiliser pour la capture,
  d'apres le workflow dwarfAlp ("ReqCaptureRawLiveStacking(ir_index=1 ou 2)") -
  correspond aux index de la table `AllowedIRFilter` (1=Astro Filter,
  2=Duo-Band Filter). Nouveau defaut choisi : 1 (Astro), le choix standard
  pour du ciel profond avec un telescope classique.
- `force_start` (CaptureRawLiveStacking) : meme logique - d'apres le
  workflow dwarfAlp, `CMD_ASTRO_CONTINUE_SHOOTING` (11050) serait plutot le
  mecanisme a utiliser APRES qu'un avertissement a deja ete souleve,
  tandis que `force_start` ici sauterait la verification en amont.

**Mis a jour** : `perform_goto(ra, dec, target, goto_only=False, rotation=None)`,
`perform_goto_stellar(target_id, target_name, force_start=False)`,
`perform_takeAstroPhoto(ir_index=1, force_start=False)` - tous les nouveaux
parametres ont des valeurs par defaut qui reproduisent exactement le
comportement d'avant (appels existants dans `main_v3.py` non impactes,
verifie par compilation).

A confirmer par capture reseau si vous testez ces nouveaux parametres -
notamment `ir_index` (qui pourrait bien etre la piece manquante pour bien
choisir le filtre lors du declenchement du stacking, plutot que de compter
uniquement sur le reglage prealable de `filterType`).

## Decouverte critique confirmee sur materiel reel : GOTO obligatoire avant le stacking

Votre capture de test (mode astro, sans cible reelle, en journee sur le
bureau) confirme exactement votre intuition. Trace exacte :

```
Send cmd >> 11005 (CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING)
receive data >> -11513
>> CODE_ASTRO_NEED_GOTO
WARNING - START_CAPTURE : ASTRO_NEED_GOTO message receive
```

**Confirme sans ambiguite** : entrer en mode astro (`perform_enter_astro_mode()`)
ne suffit PAS pour demarrer une session de stacking - le firmware exige
qu'un GOTO reel (`perform_goto()` ou `perform_goto_stellar()`) ait ete
effectue au prealable, sans quoi il renvoie `CODE_ASTRO_NEED_GOTO` (-11513).
Il existe aussi une variante plus specifique `CODE_ASTRO_NEED_GOTO_DSO`
(-11518) - possiblement quand la technique utilisee necessite
specifiquement un GOTO DSO plutot qu'un GOTO systeme solaire.

Fait interessant en marge : une seconde tentative immediate a "reussi"
(en realite `CODE_ASTRO_FUNCTION_BUSY`, signifiant qu'une capture etait
DEJA en cours), avec `target_name >> Sun` - residu d'un GOTO Soleil
effectue plusieurs sessions de test auparavant. Ca illustre un piege
potentiel : le firmware semble memoriser la derniere cible pointee meme
entre deconnexions, ce qui peut donner l'illusion trompeuse qu'un stacking
fonctionne "sans GOTO" alors qu'il exploite en realite un etat residuel
d'une session precedente.

**Ajoute** : rappel explicite dans le menu (option A9 de `main_v3.py`)
avant de demarrer une session de stacking, pour eviter de retomber dans ce
piege.

## Fusion de vos ameliorations dans main_v3.py

Vous avez enrichi `main_v3.py` avec plusieurs elements repris de l'ancien
`dwarf_test_apiV2/main.py` - tout verifie compatible V3 sans modification
necessaire (les fonctions sous-jacentes utilisees sont deja V2-inchangees
et deja correctement gerees par le dispatcher) :

- **Sous-menu "T" (Test Frames Decoding)** : reutilise `perform_decoding_test()`/
  `perform_decode_wireshark()` (dwarf_utils.py, deja presents), qui
  s'appuient sur `websockets_testV2.py`.
- **`select_solar_target()`** : table de correspondance nom -> target_id
  pour les objets du systeme solaire (Mercure=1, Venus=2, Mars=3,
  Jupiter=4, Saturne=5, Uranus=6, Neptune=7, Lune=8, Soleil=9) - tres
  utile, reprise telle quelle.
- **A11 (`perform_waitEndAstroPhoto`)** et **A12 (`perform_GoLive`)** :
  fonctions de fin de session deja V2-inchangees et deja geree par le
  dispatcher (verifie : `CMD_ASTRO_GO_LIVE` present dans `VALID_PAIRS`,
  la commande texte speciale `"ASTRO CAPTURE ENDING"` deja geree).

**Correction appliquee sur `websockets_testV2.py`** : vous aviez deja
manuellement applique le meme renommage de classes `notify.proto` qu'on
avait fait dans `websockets_utils.py`
(`ResNotifyStateAstroCalibration`->`AstroCalibrationState`,
`ResNotifyStateAstroGoto`->`AstroGotoState`,
`ResNotifyTimeLapseOutTime`->`TimeLapseOutTime`) - fichier que je n'avais
jamais retouche puisqu'il n'etait pas dans le chemin d'execution de nos
scripts jusqu'ici. Bonne prise : votre nouveau sous-menu "T" l'exerce
directement. Verifie exhaustivement (aucune classe manquante) et applique.

**Bug corrige** : `input_test()` (saisie longitude/latitude/fuseau horaire,
necessaire pour `perform_goto_stellar()`) appelait `update_config()`, qui
n'etait ni definie ni importee - aurait plante si jamais appelee. Fonction
ajoutee (portee depuis `dwarf_test_apiV2/main.py`, simple ecriture
`config.ini`, aucun protocole V3 implique) et cablee comme nouvelle option
**A0** du sous-menu Astro (reglage de la position avant tout GOTO systeme
solaire).

Teste : compilation complete, verification exhaustive des classes
protobuf de `websockets_testV2.py` (aucune manquante), tests fonctionnels
de `update_config()` (ecriture correcte dans `config.ini`) et de
`select_solar_target()` (mapping nom -> target_id verifie pour plusieurs
objets).

## Premiere capture solaire complete reussie - et bug corrige : le programme ne se termine jamais

Felicitations - premiere capture reelle de bout en bout : centrage manuel
via l'appli officielle, coupure WiFi de l'appli, reconnexion avec nos
outils, GOTO Soleil (`select_solar_target("Sun")`), suivi du tracking,
demarrage puis arret du stacking (20 sous-poses, 2 empilees) - tout a
fonctionne, confirme par la trace :

```
current_count >> 20 - stacked_count >> 2
Send cmd >> 11006 (CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING)
Success ASTRO CAPTURE ENDING
```

### Bug trouve et corrige : le processus Python ne se termine jamais

Apres l'arret reussi du stacking, plus aucune commande n'apparait dans le
log, juste du trafic de fond (ping/pong, notifications) qui continue
indefiniment - le programme reste bloque meme apres avoir choisi de
quitter.

**Cause identifiee** : dans `websockets_utils.py`, le thread qui fait
tourner la boucle d'evenements asyncio est cree SANS `daemon=True` :

```python
event_loop_thread = threading.Thread(target=run_event_loop, args=(event_loop,))
```

Un thread non-daemon empeche Python de terminer le processus tant qu'il
tourne encore - meme si la boucle principale de `main_v3.py` s'est
terminee normalement. Ce thread n'est arrete proprement que par
`disconnect_socket()` (via `stop_event_loop()`), qui n'etait JAMAIS
appelee quand on choisissait l'option `0` (Quitter) du menu principal -
elle se contentait d'un `print("Goodbye.")` puis `break`, sans jamais
deconnecter.

**Corrige** : l'option `0` du menu principal appelle desormais
`perform_disconnect()` avant de quitter. Verifie que c'est sans risque
meme si le client n'a jamais ete connecte (`disconnect_socket()` gere deja
proprement ce cas, simple avertissement, pas de plantage).

**A savoir en attendant que vous receviez la version corrigee** : appuyer
sur `D` (Deconnexion forcee) juste avant de quitter avec `0` contourne
deja le probleme, puisque `option_D()` appelait deja `perform_disconnect()`
correctement.

### Nettoyage cosmetique au passage

Le menu principal affichait `S` en double (une fois depuis la version
d'origine, une fois depuis vos ajouts) - retire le doublon. La fonction
`option_S()` avait aussi un `import json` redondant (deja importe en tete
de fichier) et un commentaire copie-colle mal etiquete ("Add your Option M
functionality here" sur la fonction S) - nettoyes.

## Precision : le GOTO Soleil/Lune fait une verification visuelle, pas juste un calcul

Vous avez signale avoir vu `SUN_MOON not found` sur un log precedent -
cause : l'objectif etait ferme. Verification precise dans le log fourni :
c'est bien `CMD_ASTRO_START_GOTO_SOLAR_SYSTEM` (11003) LUI-MEME (pas une
commande separee) qui echoue directement avec `CODE_ASTRO_SUN_MOON_NOT_FOUND`
(-11531) sur les deux premieres tentatives (18:02:23 et 18:07:18), avant
que la troisieme (18:12:29, apres centrage manuel via l'appli officielle)
ne reussisse.

**Confirme** : pour le Soleil et la Lune specifiquement (target_id 8 et 9
dans `select_solar_target()`), le GOTO effectue une **verification
visuelle** contre le flux camera, contrairement aux autres objets du
systeme solaire (Mercure a Neptune) qui semblent etre pointes par simple
calcul d'ephemeride sans confirmation visuelle. Sans le capuchon retire et
sans que la cible soit a peu pres visible pres de la position calculee, le
GOTO echoue directement.

**Ajoute** : `select_solar_target()` affiche desormais un rappel explicite
quand la cible est Soleil ou Lune, juste avant d'appeler
`perform_goto_stellar()`, pour eviter de retomber dans ce piege lors des
prochaines sessions.

## Ajoute : option A13 dans main_v3.py pour entrer en mode DSO (ou tout autre mode astro)

Question posee : quelle fonction du menu pour entrer en mode DSO (mode=2)
plutot que mode=8 (Soleil, fige dans `perform_enter_astro_mode()`) ?
Reponse : **aucune n'existait** - `option_C2` (sous-menu Camera) est la
seule entree astro du menu, et elle appelle `perform_enter_astro_mode()`
qui force mode=8.

**Ajoute** : nouvelle option **A13** dans le sous-menu Astro - "Enter astro
shooting mode", qui demande le mode et la tech (defaut 2/2 = DSO,
appuyer sur Entree suffit) et appelle directement
`perform_enter_shooting_mode(mode, tech)`, deja disponible mais jamais
exposee dans un menu jusqu'ici. Affiche un rappel de la table des modes
(2=DSO, 3=Sun/Moon parent, 4=Milky Way, 5=Star Trail, 8=Sun, 9=Moon,
10=Planet).

Numeros A0-A12 laisses inchanges (pas de renumerotation) pour ne pas
perturber vos habitudes deja prises en testant le menu.

Sequence recommandee pour valider le GOTO DSO :
```
A13 (Entree, Entree)   -> mode=2, tech=2 (DSO)
A1/A2                  -> exposition/gain astro
A3                     -> stackCount
A7 -> 1) RA/Dec         -> GOTO sur la cible DSO
A9 -> S                 -> demarrer le stacking
A10                     -> suivre la progression
A9 -> T                 -> arreter
```

## Ajoute : option A14 dans main_v3.py pour entrer en mode Solaire (Soleil/Lune/Planete)

Symetrique de A13 (DSO par defaut) : **A14** propose un raccourci vers les
modes Soleil/Lune/Planete, avec `mode=8` (Soleil, deja confirme fonctionnel
sur materiel reel) par defaut - Entree, Entree suffit. Meme mecanisme
sous-jacent (`perform_enter_shooting_mode()`), juste un defaut different
et un rappel des modes pertinents (8=Soleil, 9=Lune, 10=Planete, 3=parent
Soleil/Lune).

## Correctif : etiquette C2 trompeuse ("Astro/DSO mode") alors qu'elle fait mode=8 (Soleil)

Vous avez repere l'incoherence : le menu Camera affichait "C2. Enter
Astro/DSO mode (mode=2, tech=2)" mais `option_C2()` appelle
`perform_enter_astro_mode()`, cablee en dur sur `mode=8` (Soleil, confirme
- pas DSO generique, voir plus haut la table des modes de
`10-astronomy-functions.md`). L'etiquette datait d'avant qu'on decouvre
cette distinction et n'avait jamais ete corrigee.

**Corrige** : l'etiquette de C2 reflete desormais la realite ("mode=8,
Sun") et pointe vers les bonnes options (A13 pour DSO, A14 pour
Soleil/Lune/Planete) - le comportement de C2 lui-meme n'a pas change
(toujours `perform_enter_astro_mode()`, mode=8), seule l'etiquette
mensongere est corrigee, pour eviter que quelqu'un pense etre en DSO alors
qu'il est en mode Soleil.

## Precision : A12 (Go Live) = equivalent du bouton "Terminer" de l'appli officielle

Confirmation utile : le message `CODE_ASTRO_FUNCTION_BUSY` deja rencontre
dans vos logs precedents (quand une seconde tentative de demarrage de
stacking tombait sur une session "deja en cours") s'explique
completement. Dans l'appli officielle, a la fin d'une session, un ecran de
finalisation s'affiche avec deux boutons "Terminer"/"Editer" - **A12
(`perform_GoLive()`, `CMD_ASTRO_GO_LIVE`) est l'equivalent API du bouton
"Terminer"**. Sans cet appel, le firmware considere la session precedente
toujours "active" et refuse d'en demarrer une nouvelle
(`CODE_ASTRO_FUNCTION_BUSY`).

**Sequence complete a retenir** pour enchainer plusieurs sessions de
stacking dans la meme connexion :
```
A9 -> S   (demarrer)
A10       (suivre la progression)
A9 -> T   (arreter, ou laisser atteindre le stackCount cible)
A12       (finaliser - obligatoire avant une nouvelle session)
A7        (nouveau GOTO si nouvelle cible)
A9 -> S   (nouvelle session)
```

**Ajoute** : rappels explicites dans le menu - A9 (apres l'arret) rappelle
qu'il faut passer par A12 avant une nouvelle session, et le libelle/message
de A12 explicite desormais clairement son role ("Finish/Finalize session",
equivalent du bouton "Terminer").

## Ajoute : sous-menu Moteur complet (positions preetablies) - fait par vous-meme

Vous avez porte directement depuis `dwarf_test_apiV2/main.py` l'ensemble
des options de positionnement moteur preetabli, toutes deja
V2-inchangees et confirmees fonctionnelles sur materiel reel dans votre
session de test :

- **C** (Closed Barrel Position), **I/I3** (Init Horizontal Position,
  standard/D3), **P/P3** (Polar Align Position, standard/D3), **S/S3**
  (rotation 90° pour la 2e position d'alignement polaire, standard/D3)
  - toutes via `motor_action(id)` avec `CMD_STEP_MOTOR_RUN_TO` (14001).
- **RR/RS** (reset axe rotation/inclinaison) via `CMD_STEP_MOTOR_RESET` (14003).
- **GP** (lecture de position, D3 uniquement) via
  `CMD_STEP_MOTOR_GET_POSITION` (14011) - **c'est la fonction "motor
  position" demandee**, deja geree par le dispatcher (valeur de position
  journalisee en INFO : `receive position data >> <valeur>`).
- **PA/PS** (demarrer/arreter l'alignement polaire automatique) via
  `start_polar_align()`/`stop_polar_align()`, deja existants.

Verifie : compilation complete, toutes les fonctions presentes et
importables.

### Observation issue de votre session de test (aucun code a corriger)

Trace interessante : le tout premier `CMD_STEP_MOTOR_RUN_TO` de la session
a echoue avec `CODE_STEP_MOTOR_NEED_RESET` (-14520), puis les deux
premieres tentatives de `CMD_STEP_MOTOR_RESET` ont elles-memes echoue avec
`CODE_STEP_MOTOR_OVERTIME_GET_ABSOLUTE_POSITION_RETURN` (-14512) - un
timeout interne du firmware en attendant la position absolue pendant sa
propre sequence de reset. Apres ces deux echecs initiaux, tout s'est
stabilise : lecture de position (`GP`) et positionnements (`RUN_TO`) ont
fonctionne sans probleme sur le reste de la session (~40 minutes de tests,
positions coherentes : 12.0 puis 216.12).

**A garder en tete** (pas un bug de notre code, comportement du firmware) :
la toute premiere commande moteur d'une session semble parfois necessiter
plusieurs tentatives avant de "prendre" - possiblement une periode de
stabilisation similaire a celle deja documentee pour l'API HTTP live (voir
plus haut, "periode de chauffe"). Si `RUN_TO`/`RESET` echoue au tout debut
d'une session, retenter une ou deux fois avant de conclure a un vrai
probleme.

## Precision sur l'observation precedente : bras ferme = cause probable du timeout moteur

Vous avez precise : au moment de l'echec `CODE_STEP_MOTOR_OVERTIME_GET_ABSOLUTE_POSITION_RETURN`,
le bras du Dwarf etait encore ferme/replie. C'est une explication bien plus
probable que la "periode de chauffe" evoquee initialement.

`CMD_STEP_MOTOR_RESET` effectue vraisemblablement un homing physique
(deplacement du moteur jusqu'a une reference mecanique) pour etablir la
position absolue - si le bras est replie, ce mouvement ne peut pas
s'effectuer normalement, d'ou le timeout en attendant le retour de
position. Ca colle bien avec la chronologie observee : les deux premiers
`RESET` (bras probablement encore ferme) echouent, puis tout se stabilise
une fois `GP` reussit a 22:59:50 (bras vraisemblablement ouvert entre
temps) et reste stable sur le reste de la session.

**A retenir, corrige** : s'assurer que le bras du Dwarf est physiquement
deploye AVANT d'utiliser les commandes de reset/positionnement moteur
(`RR`, `RS`, positions preetablies `C`/`I`/`P`/`S`) - plus determinant que
le delai attendu entre connexion et premiere commande. A confirmer
definitivement en reproduisant l'echec bras ferme vs bras ouvert dans les
memes conditions, mais l'explication mecanique est nettement plus
vraisemblable qu'un probleme de timing logiciel pur.
