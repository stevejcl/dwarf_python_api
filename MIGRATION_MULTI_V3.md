# Migration Multi-Dwarf (branche `multi_V3`)

## Ce qui a été ajouté (aucun fichier existant modifié)

- `dwarf_python_api/lib/dwarf_config.py` — `DwarfConfig` (dataclass) : lit un
  couple `config.py` + `config.ini` existant (mêmes formats, aucune migration
  de vos fichiers actuels nécessaire) et produit un objet unique.
- `dwarf_python_api/lib/dwarf_session.py` — `DwarfSession` (état par
  appareil : client websocket, event loop, cache de notifications) et
  `DwarfManager` (registre de sessions, clé = `dwarf_uid`).
- `dwarf_python_api/lib/dwarf_session_socket.py` — équivalents "session-aware"
  de `connect_socket`, `init_socket`, `send_socket_message`,
  `disconnect_socket`, `get_client_status` de `websockets_utils.py`. Copie
  fidèle ligne à ligne de la logique existante (mêmes branches
  DISCONNECTED/ERROR/SLAVEMODE/TIMEOUT/WARNING) — seul `global` devient un
  attribut de `session`.

**Rien dans `websockets_utils.py` ou `dwarf_utils.py` n'est touché.** Le
comportement mono-dwarf actuel continue de fonctionner exactement comme
avant tant que vous n'appelez pas explicitement les nouvelles fonctions.

## Pourquoi `dwarf_uid` et pas `dwarf_id` comme clé

`DWARF_ID` (dans `config.py`, ex: `"4"`) est un code de **modèle** (offset -1,
cf. `config_to_dwarf_id_str`), pas un identifiant unique — tous vos Dwarf 3
partageraient la même valeur. `DWARF_UID` (ex: `"DWARF3_3AD246"`) est le
véritable numéro de série, donc la seule clé sûre pour indexer plusieurs
appareils.

## Doublon à trancher

Vos fichiers d'exemple ont deux valeurs différentes pour l'IP du Dwarf :
`config.py` → `DWARF_IP = "192.168.0.35"` et `config.ini` → `dwarf_ip =
192.168.0.252`. `DwarfConfig.from_files()` fait actuellement primer
`config.ini` (comportement identique à `start_socket()` actuel dans
`websockets_utils.py`, qui lit `data_config['ip']` via `get_config_data()` —
à vérifier si c'est bien la même source que vous souhaitez garder comme
référence unique à terme).

## Exemple concret : migrer `perform_goto`

**Avant** (`dwarf_utils.py`, actuel) :
```python
def perform_goto(ra, dec, target, goto_only=False, rotation=None):
    module_id = 3
    type_id = 0

    ReqGotoDSO_message = astro.ReqGotoDSO()
    ReqGotoDSO_message.ra = ra
    ReqGotoDSO_message.dec = dec
    ReqGotoDSO_message.target_name = target
    ReqGotoDSO_message.goto_only = goto_only
    if rotation is not None:
        ReqGotoDSO_message.rotation = rotation

    command = 11002
    response = connect_socket(ReqGotoDSO_message, command, type_id, module_id)
    ...
```

**Après** (ajout d'un paramètre optionnel, compat conservée) :
```python
from dwarf_python_api.lib.dwarf_session import get_default_session
from dwarf_python_api.lib.dwarf_session_socket import connect_socket as connect_socket_session

def perform_goto(ra, dec, target, goto_only=False, rotation=None, session=None):
    session = session or get_default_session()
    if session is None:
        log.error("Dwarf API: no DwarfSession available (call DwarfManager.add() first)")
        return False

    module_id = 3
    type_id = 0

    ReqGotoDSO_message = astro.ReqGotoDSO()
    ReqGotoDSO_message.ra = ra
    ReqGotoDSO_message.dec = dec
    ReqGotoDSO_message.target_name = target
    ReqGotoDSO_message.goto_only = goto_only
    if rotation is not None:
        ReqGotoDSO_message.rotation = rotation

    command = 11002
    response = connect_socket_session(session, ReqGotoDSO_message, command, type_id, module_id)
    ...
```

Le diff est mécanique : ajouter `session=None` aux paramètres, résoudre
`session = session or get_default_session()` en première ligne, remplacer
l'appel à `connect_socket(...)` par `connect_socket_session(session, ...)`.
Même chose pour tous les `perform_*_v3` qui appellent `connect_socket`.

## Pourquoi ce n'est PAS fait automatiquement sur les ~80 fonctions `perform_*`

`dwarf_utils.py` fait 3074 lignes et contient de la logique validée sur
matériel réel (timing, séquences de handshake, cas d'erreur spécifiques à
chaque modèle). Un remplacement automatique en masse, sans repasser chacune
au banc d'essai, risquerait de réintroduire silencieusement un bug du genre
de ceux que vous avez déjà chassés (le `self.command` manquant, le mode
Solar par défaut...). Je recommande de migrer fonction par fonction, dans
l'ordre d'usage réel (goto, prise de vue, statut), en validant sur le Mini
et le D3 en parallèle à chaque étape plutôt qu'en un seul gros commit.

## Fonctions migrées à ce jour (fait, testé)

- **GOTO / astro** : `perform_goto`, `perform_takeAstroPhoto`,
  `perform_waitEndAstroPhoto` (+ `perform_waitRetryEndAstroPhoto`)
- **Mode photo** : `perform_switch_shooting_mode`, `perform_enter_camera`,
  `perform_switch_shooting_tech`, `perform_set_preview_quality`,
  `perform_enter_shooting_mode`, `perform_enter_astro_mode`,
  `perform_enter_photo_mode`, `perform_takePhoto`

Toutes acceptent `session=None`, exactement selon le patron décrit plus
haut. Le patch cumulatif est `0001-multi-dwarf-session-support.patch` (à
appliquer avec `git apply` sur `dwarf_python_api/lib/dwarf_utils.py`) ou
`dwarf_utils.py` fourni tel quel.

Testé (sans matériel, `connect_socket_session` mocké) :
- `perform_goto(..., session=s_mini)` / `s_d3` : aucune fuite, fallback
  mono-dwarf correct sans `session=`.
- Chaîne complète `perform_enter_photo_mode(session=...)` →
  `perform_takePhoto(session=...)` : les 5 commandes de la séquence
  (`SWITCH_SHOOTING_MODE` 16402, `ENTER_CAMERA` 16404,
  `SWITCH_SHOOTING_TECH` 16403, `SET_PREVIEW_QUALITY` 10050,
  `PHOTOGRAPH` 10002) sont routées vers la bonne session de bout en bout
  pour 2 appareils simulés en parallèle, sans mélange.

**Point important** : le fallback mono-dwarf (`get_default_session()`)
s'appuie sur le **singleton module-level** `_manager` de `dwarf_session.py`
- celui que renvoie `get_manager()` - pas sur n'importe quelle instance de
`DwarfManager()` que vous créeriez de votre côté. Si vous créez votre
propre `DwarfManager()`, enregistrez vos sessions via
`get_manager().add(config, make_default=True)` (ou `set_default_session()`)
pour que le code pas encore migré (qui ne passe pas `session=`) les
retrouve automatiquement.

## BLE : synchronisation directe avec la session (correctif de terrain)

Test réel effectué : 2 Dwarf, un `config.py`/`config.ini` avec un `dwarf_uid`
initialement faux, puis correction via BLE - et un cas où l'IP d'un
appareil change alors qu'une session était déjà connectée, l'ancien
appareil restant allumé et répondant toujours à l'ancienne IP. Résultat
observé : le programme continuait de parler au **mauvais** appareil
physique, silencieusement.

Cause : `DwarfConfig` ne lit `config.py`/`config.ini` qu'une fois, à la
création de la session. Le flux BLE (`connect_direct_bluetooth.py`) réécrit
`ip`/`dwarf_id`/`dwarf_uid` dans ce même fichier partagé, mais une session
déjà créée ne relit jamais ce fichier - elle garde son ancienne IP en
mémoire et son ancienne connexion websocket ouverte.

**Fichiers ajoutés/modifiés :**
- `dwarf_ble_session.py` (nouveau) - `apply_ble_discovery(session, ip_address, dwarf_id, dwarf_uid)` :
  applique directement un résultat de découverte BLE sur la session, sans
  passer par une relecture de `config.py`. Si l'IP change alors qu'une
  connexion est déjà ouverte, l'ancien socket est déconnecté avant
  d'appliquer la nouvelle IP - plus de risque de continuer à parler à
  l'ancien appareil resté allumé.
- `dwarf_session.py` - ajout de `DwarfManager.reindex(session, old_uid)` :
  re-indexe une session dans le registre quand son `dwarf_uid` devient
  connu/corrigé après coup (votre 1er cas : uid faux au départ, corrigé
  ensuite par BLE) - sans ça, `manager.get(<bon_uid>)` continuerait à lever
  `KeyError` puisque l'entrée resterait indexée sous l'ancienne clé.
- `connect_direct_bluetooth.py` (patch `0002-ble-session-aware.patch`) -
  `connect_ble_dwarf()`/`connect_ble_direct_dwarf()` acceptent un
  `session=None` optionnel. **Le type de retour (booléen) et l'écriture
  dans `config.py` sont inchangés** - aucun appelant existant
  (`astro_dwarf_session_UI.py`, `astro_dwarf_scheduler.py`, qui font tous
  les deux `if result:` sur cette valeur) n'est affecté tant que `session`
  n'est pas explicitement passé.

Testé (sans matériel, `connection_state` simulé) :
- UID faux → UID correct découvert par BLE : re-indexation réussie, plus de
  clé fantôme dans le manager.
- Session déjà connectée + BLE annonce une IP différente pour le même
  `dwarf_uid` : l'ancien socket est bien déconnecté avant que la nouvelle
  IP soit appliquée.

Usage dans votre flux d'appairage multi-dwarf :
```python
from dwarf_ble_connect.lib.connect_direct_bluetooth import connect_ble_direct_dwarf

connect_ble_direct_dwarf(ble_psd, ssid, pwd, auto_select, session=my_session)
# my_session.config.dwarf_ip / dwarf_uid sont maintenant à jour,
# et l'ancienne connexion (si elle existait) a été proprement fermée.
```

## Vérification d'identité sans BLE : `/deviceInfo` (fait, testé)

Confirmé par vous : `GET http://<ip>:8082/deviceInfo` renvoie un bloc
`data` avec `deviceName` (le même format de chaîne que celui utilisé par
BLE pour `dwarf_uid` - `dwarf_lib_ble.py` fait
`connection_state["device_dwarf_uid"] = dwarf_device.name`), `sn`,
`deviceId`, `mac`/`macAddress`, `staIpAddress`, etc.

**Attention sécurité (confirmée sur votre matériel)** : cet endpoint HTTP
n'est pas authentifié et renvoie aussi `devicePwd` et `staWifiPwd` en
clair. `perform_get_device_info_http()` ne logue jamais la réponse
complète pour cette raison - seuls `deviceName`/`sn` sont utilisés dans les
messages de log de `verify_device_identity()`.

**Nouvelles fonctions dans `dwarf_utils.py`** (patch cumulatif
`0001-multi-dwarf-session-support.patch`) :
- `perform_get_device_info_http(session=None)` - GET `/deviceInfo`,
  session-aware comme les autres fonctions HTTP existantes (qui, elles,
  restent mono-dwarf pour l'instant - `_get_dwarf_ip()` global,
  non traité ici).
- `verify_device_identity(session, raise_on_mismatch=False)` - compare
  `deviceName` (retourné par l'appareil) à `session.config.dwarf_uid`.
  Retourne `True` (confirmé), `False` (mismatch confirmé - mauvais
  appareil physique) ou `None` (endpoint injoignable, donc non vérifié -
  à traiter avec la même prudence qu'un mismatch, pas comme un succès).

C'est le filet de sécurité pour le chemin "appareil déjà allumé et en
STA, connexion directe sans repasser par BLE" - celui que
`apply_ble_discovery()` ne peut pas couvrir puisqu'aucun BLE ne s'exécute
dans ce cas.

Testé (JSON réel que vous avez fourni, requests mocké) :
- Rejoue exactement votre cas (`config` dit `DWARF3_3AD246`, l'appareil à
  cette IP est en fait `DWARF_mini_19A608`) → `verify_device_identity`
  retourne `False` avec un message explicite citant les deux noms + le `sn`.
- Cas où `dwarf_uid` correspond bien → retourne `True`.

Usage recommandé, avant tout `perform_enter_photo_mode`/`perform_goto`/etc.
sur une session qui n'a pas été fraîchement confirmée par BLE dans cette
exécution :
```python
from dwarf_python_api.lib.dwarf_utils import verify_device_identity

if verify_device_identity(session, raise_on_mismatch=True) is not True:
    # abort - mauvais appareil ou identité non confirmée
    ...
```

**Mapping `deviceId` confirmé** (référentiel de `/deviceInfo`, DIFFÉRENT de
l'offset -1 utilisé par `config.py`'s `DWARF_ID` -
`config_to_dwarf_id_str`/`int`) :
- 1 = Dwarf II
- 2 = Dwarf 3
- 3 = réservé à un "Dwarf 3 Pro" non sorti à ce jour
- 4 = Dwarf Mini

Relation confirmée : `config.py` `DWARF_ID` (stocké) = `/deviceInfo`
`deviceId` + 1 (D2: 1→2, D3: 2→3, D3 Pro réservé: 3→4, Mini: 4→5 -
cohérent avec la mémoire précédente "Dwarf Mini device ID confirmé = 5").

Documenté dans `dwarf_utils.py` (`DEVICE_INFO_HTTP_MODEL_MAP` + docstring
de `perform_get_device_info_http`). `verify_device_identity()` utilise
maintenant aussi ce mapping comme **signal secondaire** : si `deviceName`
correspond mais que `dwarf_model_id` (config) ne correspond pas à
`deviceId+1` (réel), un `WARNING` est émis (config interne incohérente)
sans faire échouer la vérification principale, qui reste basée sur
`deviceName`.

## `connect_bluetooth_cmd.py` : écriture redirigée vers le bon fichier (fait, testé)

Cause racine du "je me reconnecte avec la bonne IP mais pas mis à jour" :
`connect_bluetooth_cmd.py` appelait `connect_ble_direct_dwarf(...)` sans
`session=` (normal, script mono-dwarf préexistant) - mais **même avec
`session=`, l'écriture disque (`update_config_data`) aurait quand même
ignoré un chemin `config.py` spécifique à un appareil** : elle cible
toujours le `CONFIG_FILE` global de `get_config_data.py` (`'config.py'` par
défaut), sauf si `set_config_data()` a été appelé avant pour rediriger.

**Fix** : `connect_bluetooth_cmd.py` accepte maintenant `--config-py`. S'il
est fourni, le script appelle `set_config_data()` avant de lancer BLE, ce
qui redirige l'écriture (`ip`/`dwarf_id`/`dwarf_uid`) vers exactement ce
fichier - avec des `tmp`/`lock` dérivés du même chemin, pour que deux
connexions BLE simultanées sur deux appareils différents n'entrent pas en
collision sur un fichier `.tmp`/`.lock` partagé. À la fin, le script
relit et affiche clairement `dwarf_uid=... ip=... saved to <chemin absolu>`,
pour qu'une incohérence saute aux yeux immédiatement plutôt que d'être
découverte plus tard dans un autre script.

**Ne change rien à l'usage existant** : sans `--config-py`, comportement
identique à avant (écrit dans `./config.py`).

Testé (BLE simulé - le vrai module `connect_direct_bluetooth.py` importe du
code spécifique Windows/`bleak.backends.winrt`, impossible à exécuter tel
quel hors Windows) :
```
DWARF_IP = "192.168.0.150"      # avant: 192.168.0.35
DWARF_UID = "DWARF_mini_19A608"  # avant: DWARF3_3AD246
...
Bluetooth -> WiFi connection succeeded. dwarf_uid='DWARF_mini_19A608' ip='192.168.0.150' saved to /tmp/.../config_mini.py
```

Usage multi-dwarf recommandé :
```bash
python connect_bluetooth_cmd.py --config-py config_mini.py --ssid "..." --pwd "..." --select "DWARF_mini_19A608"
python connect_bluetooth_cmd.py --config-py config_d3.py   --ssid "..." --pwd "..." --select "DWARF3_3AD246"
# puis, dans chaque script d'usage:
python test_multi_v3_photo.py --config-py config_mini.py --config-ini config_mini.ini
```

**Piège d'import évité en cours de route** : mettre `import
dwarf_python_api.get_config_data` en tout premier import du fichier casse
un cycle d'import fragile préexistant entre `get_config_data.py` et
`my_logger.py` (`AttributeError: cannot access submodule...`). Gardé en
dernier import, comme dans l'ordre d'origine du fichier.

## Récupération automatique d'IP périmée via BLE (fait, testé)

Cas décrit : reconnexion du D3 sur sa bonne adresse (ex. `.252`), mais la
session/config en main a encore l'ancienne (`.35`, qui ne répond plus). Au
lieu d'échouer sur cette IP morte, le bon comportement est : détecter
l'échec → rafraîchir l'IP via un BLE ciblé sur ce `dwarf_uid` → revérifier
sur la **nouvelle** IP, pas l'ancienne.

**`ensure_device_reachable(session, ble_ssid=None, ble_pwd=None, ble_psd=None, raise_on_failure=False)`**
(dans `dwarf_utils.py`) :
1. `verify_device_identity(session)` sur l'IP actuelle.
2. Si pas de correspondance confirmée (`False` ou `None`) et que des
   identifiants WiFi sont fournis : relance un BLE ciblé
   (`auto_select=session.dwarf_uid` - pas de choix manuel même si plusieurs
   Dwarf sont visibles) via `connect_ble_direct_dwarf(..., session=session)`,
   ce qui met à jour `session.config.dwarf_ip` via `apply_ble_discovery`
   et déconnecte toute connexion périmée.
3. Revérifie l'identité - cette fois sur l'IP fraîchement découverte.

Sans `ble_ssid`/`ble_pwd`, se comporte exactement comme
`verify_device_identity()` seul (aucune tentative de récupération) - pas
de changement de comportement si vous ne voulez pas de ce mécanisme.

Testé (BLE + HTTP simulés) :
- Sans identifiants BLE : échec sur l'ancienne IP morte → `None`
  (comportement inchangé).
- Avec identifiants BLE : détecte que `.35` ne répond plus → BLE ciblé
  trouve le device à `.252` → `session.config.dwarf_ip` mis à jour → 
  revérification réussie sur `.252` → `True`.

Intégré dans `test_multi_v3_photo.py` via `--ble-ssid`/`--ble-pwd`/`--ble-psd` :
```bash
python test_multi_v3_photo.py --ble-ssid "MonWifi" --ble-pwd "monmotdepasse"
```

## Correctif de régression : ordre config.py/config.ini (ma faute)

**Ce qui a causé le comportement observé** (`config.py` disait 252,
`config.ini` disait encore 35, la session chargeait 35) : une copie groupée
que j'avais faite plus tôt (`cp multi_v3_foundation/*.py ... outputs/`)
avait écrasé le correctif d'ordre de priorité par une version obsolète
restée dans mon dossier de travail (`ini_get("dwarf_ip") or
py_values.get("ip")` au lieu de l'inverse). Pas un bug de fond, pas un
souci côté fichier - une régression de mon fait pendant la conversation.
Corrigé et reverifié (`dwarf_config.py`).

## `resolve_dwarf_ip()` : vérifier les deux candidats connus avant BLE (fait, testé)

Stratégie proposée et implémentée : plutôt que de ne vérifier qu'une seule
adresse et échouer, `DwarfConfig` conserve maintenant les deux candidats
d'IP (`dwarf_ip` = primaire, `config.py` ; `alternate_dwarf_ip` = celui
écarté, généralement `config.ini`, jamais mis à jour par BLE et pouvant
donc légitimement diverger). `resolve_dwarf_ip(session)` :

1. Vérifie `dwarf_ip` (primaire) via `/deviceInfo`. Si confirmé -> terminé.
2. Sinon, essaie `alternate_dwarf_ip` (déconnexion propre de toute
   connexion déjà ouverte avant de basculer). Si confirmé -> adopté comme
   nouveau `dwarf_ip`.
3. Si aucun des deux ne confirme le bon `dwarf_uid` (y compris le cas où
   une adresse répond mais avec le **mauvais** appareil - ex. deux Dwarf
   ayant échangé leurs IP) -> restaure la primaire, retourne `False` :
   on s'arrête, on n'envoie rien.

N'utilise PAS BLE - uniquement les candidats déjà connus des fichiers de
config. Pour une IP totalement inconnue des deux fichiers, `ensure_device_reachable()`
reste disponible en repli (BLE ciblé sur le `dwarf_uid`).

Testé :
- Cas réel (primaire 252 correct, alternate 35 périmé) -> confirmé
  directement sur 252, sans même essayer 35.
- Cas mixup (une adresse répond mais c'est le mauvais appareil physique) ->
  `False`, adresse restaurée à la primaire, rien n'est envoyé.

Intégré dans `test_multi_v3_photo.py` : `resolve_dwarf_ip()` tourne
d'abord (aucun BLE), et seulement si ça échoue ET que `--ble-ssid`/`--ble-pwd`
sont fournis, `ensure_device_reachable()` prend le relais.

## Correctif : `/deviceInfo` est en POST, pas GET (confirmé sur D3 réel)

Cause du "MISMATCH" observé alors que la config était en fait correcte :
`perform_get_device_info_http()` utilisait `requests.get()`, qui renvoie
404 sur cet endpoint. Confirmé par votre test manuel : **POST** fonctionne
et renvoie les bonnes données (`deviceName='DWARF3_3AD246'`,
`staIpAddress='192.168.0.252'` - votre config était déjà correcte, seul
l'appel HTTP était fautif).

En prime, `resolve_dwarf_ip()` distingue maintenant deux cas qui
produisaient le même message trompeur ("MISMATCH") :
- **Injoignable des deux côtés** (comme dans votre run - 404/timeout) ->
  retourne `None` (non confirmé, PAS un mismatch avéré).
- **Un candidat répond mais c'est le mauvais appareil** -> retourne
  `False` (mismatch confirmé, vrai arrêt).

`test_multi_v3_photo.py` affiche donc désormais le bon message selon le
cas (`None` -> "pas joignable, on continue sans confirmation" ;
`False` -> "MISMATCH, on arrête").

## Retrait de la vérification secondaire `dwarf_model_id`/`deviceId+1`

Contredite par un vrai croisement matériel (D3 réel : `/deviceInfo`
`deviceId=2`, et `config.py DWARF_ID=2` - **pas** de +1 ici). En creusant
`dwarf_lib_ble.py`, le BLE écrit `DWARF_ID` **brut**, avec la même
numérotation que `/deviceInfo` (1=D2, 2=D3, 4=Mini, détecté par UUID de
service GATT) :
```python
DWARFII_SERVICE_UUID   -> device_dwarf_id = 1
DWARF3_SERVICE_UUID    -> device_dwarf_id = 2
DWARFMINI_SERVICE_UUID -> device_dwarf_id = 4
```

**Précision apportée ensuite** : `config_to_dwarf_id_str()`/`_int()`
(`get_config_data.py`) ne sont **pas** une convention concurrente pour le
même usage - c'est une transformation `+1` volontaire et cohérente,
utilisée dans `astro_dwarf_session`/`main_v3.py` pour obtenir un "numéro
logique" d'affichage/branchement (2=Dwarf II, 3=Dwarf 3, 5=Dwarf Mini -
`DWARF_NAME_MAP`, branches spécifiques au modèle pour le filtre IR, etc.),
**différent** de la valeur brute stockée dans `config.py`, elle-même
identique à `/deviceInfo`'s `deviceId` sans décalage.

**Vérification secondaire réintégrée**, corrigée (comparaison directe
`dwarf_model_id == deviceId`, sans `+1`) - testée et silencieuse sur vos
deux appareils réels (D3 : `2`/`2` ; Mini : `4`/`4`), se déclenche
uniquement sur une vraie incohérence.

## Nouveau lot migré : statut, GOTO stellaire, réglages caméra (fait, testé)

- `perform_getstatus`, `unset_HostMaster`, `set_HostMaster`,
  `perform_get_device_state_info`
- `perform_goto_stellar` (compagnon de `perform_goto` - note :
  `read_longitude()`/`read_latitude()` qu'elle appelle ne sont pas encore
  session-aware, lisent toujours `config.ini` directement - sans
  conséquence en mono-dwarf, à traiter avant de vouloir des
  latitude/longitude différentes par session)
- Réglages caméra V3 : `perform_set_exposure_v3`, `perform_set_exposure_by_name_v3`,
  `perform_set_gain_v3`, `perform_set_gain_by_camera_v3`,
  `perform_set_astro_exposure_v3`, `perform_set_astro_exposure_by_name_v3`,
  `perform_set_astro_gain_v3`
- `perform_auto_focus_v3`

Testé : séquence `getstatus`/`get_device_state_info`/réglage
exposure-astro/réglage gain-astro/autofocus sur deux sessions simulées en
alternance, aucune fuite entre appareils.

**Non migré pour l'instant, sciemment** : `perform_read_exposure_v3`,
`perform_read_gain_v3`, `perform_read_all_camera_params_v3`. Ces fonctions
lisent via `get_camera_param_v3()` (`websockets_utils.py`), qui s'appuie
sur un **cache de notifications passif global** - pas encore session-scopé
(même famille de problème que `previous_values` qu'on avait dû sortir du
global pour `get_client_status()`). Ajouter `session=None` sans d'abord
scoper ce cache serait trompeur : le paramètre existerait mais ne ferait
rien. À traiter ensemble dans un prochain lot.

État global : **~38 fonctions migrées**, ~50 restantes (surtout : réglages
image/WB/burst/timelapse `perform_set_*_v3`, fonctions HTTP live restantes,
`perform_get_all_camera_setting`/`perform_update_camera_setting` V2-style,
tests/diagnostics `perform_decoding_test`/`perform_decode_wireshark`).

## Cache de notifications : session-aware (fait, testé)

Bonne surprise : `cameraParamsDwarf` était déjà un **attribut par
instance** de `WebSocketClient`, pas un vrai global partagé - il suffisait
d'arrêter de lire la variable globale `client_instance` et de lire
`session.client_instance` à la place. Pas de refonte de cache nécessaire.

- `dwarf_session_socket.py` : nouvelle `get_camera_param_v3(session, param_id)`.
- `dwarf_utils.py` : `perform_read_exposure_v3`, `perform_read_gain_v3`,
  `perform_read_all_camera_params_v3` acceptent maintenant `session=None`.

Testé : deux sessions avec des caches `cameraParamsDwarf` différents pour
le **même** `param_id` (Mini="0.5", D3="1/4") - chaque lecture retourne
bien sa propre valeur, aucun mélange.

État global : **~41 fonctions migrées**.

## Vos deux corrections (branche non-multi) intégrées

Fournies via `websockets_utils.py`/`dwarf_utils.py` uploadés - intégrées
telles quelles, aucun rapport avec le multi-dwarf mais utiles pour tout le
monde :

1. **`websockets_utils.py`** - fix d'un blocage sur `perform_stop_goto` :
   la notification `CMD_NOTIFY_STATE_ASTRO_TRACKING` avec
   `ASTRO_STATE_STOPPED` pendant un `CMD_ASTRO_STOP_GOTO` n'était pas
   reconnue comme complétant la commande. Comme cette logique vit dans
   `WebSocketClient` (partagée par le mono-dwarf et par vos
   `DwarfSession`), le fix profite automatiquement au multi-dwarf - aucune
   duplication nécessaire. Vérifié identique bit-à-bit à votre version.
   Patch séparé : `0003-websockets-utils-stop-goto-fix.patch`.

2. **`dwarf_utils.py`** - fix `perform_set_ir_filter_v3` : une chaîne
   numérique (`"1"`) était traitée comme un nom à chercher dans la table
   IR au lieu d'un index, retombant silencieusement sur l'index 0 à chaque
   fois qu'un appelant passait une valeur de config stringifiée. Testé :
   `"1"` → index 1 (avant : 0), `2` → 2, `"Astro Filter"` → 1 (lookup par
   nom toujours fonctionnel).

## Nouveau lot migré : image (WB/brightness/contrast/saturation/hue/sharpness), burst, timelapse (fait, testé)

Encore une fois, seules 2 fonctions appellent le socket
(`perform_set_wb_v3`, `perform_set_image_param_v3`) - toutes les autres
(15 fonctions au total dans ce lot) sont des enveloppes fines qui
délèguent. `session=None` propagé partout, y compris à travers les
enveloppes "by_name" à plusieurs niveaux (ex.
`perform_set_timelapse_duration_by_name_v3` → `perform_set_timelapse_duration_v3`
→ `perform_set_image_param_v3`).

Testé : 4 réglages différents (WB par nom, brightness, burst interval par
nom, timelapse duration par nom) routés vers 2 sessions distinctes, aucune
fuite même à travers les chaînes d'enveloppes.

État global : **~55 fonctions migrées** sur ~95 fonctions `perform_*`/liées
au total.

## Nouveau lot migré : burst/record/timelapse start/stop (fait, testé)

`perform_start_burst_v3`, `perform_stop_burst_v3`, `perform_start_record_v3`,
`perform_stop_record_v3`, `perform_start_timelapse_v3`,
`perform_stop_timelapse_v3` - patron identique, simple. Testé sur 2
sessions en alternance, aucune fuite.

État global : **~61 fonctions migrées**.

## Nouveau lot migré : système/RGB, joystick moteur, réglages astro restants (fait, testé)

`perform_reboot`, `perform_powerdown`, `perform_powerOpenRGB`,
`perform_powerCloseRGB`, `perform_powerIndOn`, `perform_powerIndOff`,
`perform_motor_joystick_v3`, `perform_motor_joystick_stop_v3`,
`perform_set_astro_stack_count_v3`, `perform_set_astro_mosaic_count_v3`,
`perform_set_bool_param_v3`, `perform_set_astro_auto_calibration_v3`.
Testé sur 2 sessions en alternance (8 appels), aucune fuite. Nettoyage
mineur au passage : un `return False` mort en double supprimé dans
`perform_motor_joystick_stop_v3`.

**Toujours pas migré, sciemment** : `perform_set_ir_filter_v3` délègue à
`perform_update_camera_setting`, une grosse fonction V2-style à plusieurs
branches (exposure/gain/IR/wb...) avec plusieurs appels socket internes -
mérite un lot dédié plutôt qu'un fix précipité.

État global : **~72 fonctions migrées**.

## Nouveau lot migré : get-all V2 non-répondantes, HTTP restantes, statut stacking (fait, testé)

`perform_get_all_camera_setting`, `perform_get_all_feature_camera_setting`,
`perform_get_all_camera_wide_setting` (V2 non-répondantes en V3, migrées
quand même pour cohérence/référence future), `perform_get_default_params_config_http`,
`perform_get_param_and_setting_http`, `perform_read_camera_params_http_v3`,
`perform_read_astro_stacking_status_v3` (utilise maintenant
`get_client_status_session` au lieu du cache global quand `session` est
fourni).

Testé : 6 fonctions routées entre 2 sessions (HTTP + socket mélangés),
plus lecture du statut de stacking directement depuis le cache dédié
d'une session (`current_count=42` retrouvé correctement).

**Restant, sciemment groupé pour un futur lot dédié** :
`perform_set_ir_filter_v3` + `perform_update_camera_setting` +
`perform_get_camera_setting` + `perform_update_all_camera_setting` -
grosses fonctions V2-style à plusieurs branches et plusieurs appels socket
internes chacune. `perform_decoding_test`/`perform_decode_wireshark` sont
des diagnostics locaux (pas de connexion réseau), `session` n'a pas de
sens pour elles.

État global : **~79 fonctions migrées**.

## Réconciliation avec votre refactor V2 (fait, testé)

Vous avez déplacé les fonctions V2 non-répondantes/superflues
(`perform_get_all_camera_setting`, `perform_get_camera_setting`,
`perform_update_camera_setting`, etc.) vers un nouveau `dwarf_utilsV2.py`,
réécrit `perform_set_ir_filter_v3` en appel socket direct, corrigé un
bug de nommage (`noretry`→`retry` sur `perform_waitEndAstroWidePhoto`), et
ajouté 4 nouvelles fonctions V3 (`perform_start_mosaic_v3`,
`perform_set_astro_stack_format_v3`, `perform_set_astro_display_source_v3`,
`perform_set_astro_stack_binning_v3`).

Réconcilié par fusion à 3 voies (`git merge-file`) entre la version
pristine, ma version migrée, et votre nouvelle base - 8 conflits résolus
un par un. Deux problèmes détectés et corrigés au passage :

1. **Import manquant** : `dwarf_utils.py` utilise encore `get_result_value`
   (RGB/power) mais sa définition est passée dans `dwarf_utilsV2.py` sans
   import ajouté - aurait provoqué un `NameError` à l'exécution. Corrigé
   par un import différé (local à chaque fonction RGB/power) plutôt qu'en
   tête de fichier, pour éviter un import circulaire
   (`dwarf_utilsV2.py` importe lui-même `format_double` depuis
   `dwarf_utils.py`).
2. **`CMD_ASTRO_START_TELE_MOSAIC`** n'existe pas encore dans le
   `protocol_pb2.py` de mon sandbox - normal, cette constante doit être
   dans votre `protocol.proto` mis à jour, non inclus dans cet upload.
   Fonctionnera chez vous, juste impossible à tester ici sans ce fichier.

`dwarf_utilsV2.py` et `__init__.py` repris tels quels (aucune migration
`session=`, comme demandé - fonctions legacy).

Testé : IR filter (nouvelle implémentation + fix), `waitEndAstroWidePhoto`
(paramètre renommé), mosaïque, les 3 nouveaux réglages astro, RGB power -
tout routé correctement entre 2 sessions.

État global : **~88 fonctions migrées**, `dwarf_utils.py` synchronisé avec
votre dernière base.

## Migration des `read_*` (config.ini) : le dernier verrou multi-dwarf (fait, testé)

Les 19 fonctions `read_*` (longitude, latitude, timezone, exposure, gain,
IR, binning, format, count, wide_exposure, wide_gain, et les 8
`read_bluetooth_*`) lisaient toutes `config.ini` directement, indépendamment
de toute session - c'était le verrou signalé dès `perform_goto_stellar`
("read_longitude()/read_latitude() NOT YET session-aware"). Toutes
acceptent maintenant `session=None` : si fourni, lecture directe depuis
`session.config.<champ>` (déjà chargé par `DwarfConfig.from_files()`) au
lieu de reparser `config.ini`.

Ajout au passage : champ `format` manquant dans `DwarfConfig` (nécessaire
pour `read_camera_format`).

**`perform_goto_stellar` mise à jour** pour propager `session` à
`read_longitude()`/`read_latitude()` - c'est maintenant la première
fonction GOTO véritablement multi-dwarf de bout en bout, avec
latitude/longitude propres à chaque appareil.

Testé : deux sessions avec des latitude/longitude/exposure/gain/SSID WiFi
différents - chaque lecture retourne bien la valeur de la bonne session, et
`perform_goto_stellar(session=s_mini)` / `perform_goto_stellar(session=s_d3)`
envoient chacune leurs propres coordonnées.

**Note de compatibilité** : les valeurs par défaut de `DwarfConfig` (ex.
`exposure="30"`) diffèrent légèrement du comportement mono-dwarf d'origine
qui retournait `False` si la clé était absente du fichier - une session
retourne toujours la valeur par défaut du dataclass plutôt que `False`
dans ce cas précis. Sans impact pratique (un `config.ini` réel a
quasiment toujours ces clés), mais à garder en tête.

État global : **~107 fonctions/lectures migrées**. La quasi-totalité de
`dwarf_utils.py` est maintenant multi-dwarf-compatible.

## Correctif propre : `get_result_value()` sans import circulaire

Vous avez déplacé `get_result_value()` dans `dwarf_utils.py` (juste après
`format_double()`, dont elle dépend), et fait importer `dwarf_utilsV2.py`
depuis là - sens de dépendance correct (le legacy dépend du moderne).
Fusionné (0 conflit cette fois) et mon contournement précédent (import
différé local à 4 fonctions + commentaire sur l'import circulaire) retiré,
devenu inutile.

Testé : import du package propre, `get_result_value` bien la même
fonction des deux côtés (pas de duplication), et les 4 fonctions RGB/power
qui en dépendent (`perform_powerOpenRGB` etc.) routent toujours
correctement entre sessions.

État global inchangé : **~107 fonctions migrées**, rien perdu dans cette
réconciliation.

## `astro_dwarf_session` : session-threading complet (fait, testé)

Deux mises à jour de votre part sont arrivées en cours de route et ont été
réconciliées par fusion à 3 voies (`git merge-file`), sans rien perdre :
votre bascule IR/binning/count vers les fonctions V3
(`perform_set_ir_filter_v3`/`perform_set_astro_stack_binning_v3`/`perform_set_astro_stack_count_v3`),
les nouveaux modes solaires (Sun/Moon/Planet), l'autofocus infini forcé
avant EQ Solving, et le nettoyage de `perform_get_all_feature_camera_setting`.

**`astro_dwarf_scheduler.py`** :
- `CURRENT_SESSION` (global, miroir de `CURRENT_CONFIG_NAME`) +
  `get_current_session()`.
- `setup_new_config()` construit/retrouve désormais une `DwarfSession` via
  `DwarfManager`, en plus de rediriger `set_config_data()` (comportement
  inchangé). **Réutilise** la session existante si ce `dwarf_uid` a déjà
  été vu (préserve une connexion déjà ouverte au lieu de forcer une
  reconnexion à chaque bascule de profil) - testé explicitement.
- Les deux appels à `start_dwarf_session(...)` passent maintenant
  `session=get_current_session()`.

**`dwarf_session.py`** (le vôtre, orchestration de session) :
`start_dwarf_session`, `select_solar_target`, `print_camera_data`,
`print_wide_camera_data`, `start_polar_align`/`stop_polar_align` (dans
`dwarf_python_api`) acceptent tous `session=None` et le propagent à
absolument tous leurs appels `perform_*` internes - plus aucun appel
"orphelin" retombant sur le mono-dwarf implicite dans le chemin principal.

Testé : bascule `Default` → `Mini` → `Default` réutilise bien la même
session (connexion préservée) ; une session complète (init, GoLive, entrée
mode astro, GOTO manuel) exécutée avec `session=s_d3` route 100% de ses 7
commandes vers `DWARF3_3AD246`, zéro fuite vers le global.

## BLE interactif (`connect_ble_dwarf_win`) : session-aware (fait, testé)

Même patron que `connect_bluetooth_cmd.py` : `connect_ble_dwarf_win(...,
session=None)` applique la découverte BLE (ip/dwarf_id/dwarf_uid) à la
session fournie via `apply_ble_discovery()`, en plus de l'écriture
`config.py` existante (comportement inchangé sans `session`).

Propagé de bout en bout :
- `connect_bluetooth.py` : `connect_bluetooth_win()`/`connect_bluetooth_cmd()`
  acceptent et transmettent `session=None`.
- `astro_dwarf_scheduler.py` : `start_connection()` et `start_STA_connection()`
  acceptent `session=None` (cette dernière lit `session.config.dwarf_ip`/
  `dwarf_model_id` directement si fournie, sinon `config.py` global comme
  avant) ; `perform_time`/`perform_timezone`/`perform_set_location` déjà
  session-aware en profitent automatiquement.
- `astro_dwarf_session_UI.py` : les deux points d'entrée réels de l'UI
  (`bluetooth_connect_thread`, `run_scheduler`) passent maintenant
  `session=get_current_session()`.

**Non touché, sciemment** : les 3 appels `start_connection()`/
`start_STA_connection()` dans le bloc `if __name__ == "__main__":` de
`astro_dwarf_scheduler.py` (lancement CLI autonome du script, mono-dwarf
par nature, sans notion de profil sélectionné).

Testé : `apply_ble_discovery` re-indexe bien une session dont l'uid était
initialement faux/inconnu (cas réel déjà rencontré) ; et confirmé que
`get_current_session()` (via `setup_new_config()`) et `get_manager()`
(utilisé en interne par le flux BLE) pointent bien vers le **même**
singleton - donc une connexion BLE sur le profil actif de l'UI atterrit
bien sur la bonne session, pas une copie déconnectée.

État global : la chaîne complète config → session → socket → BLE est
maintenant cohérente de bout en bout pour le multi-dwarf.

## Correctif critique avant vos tests UI : session figée pour le scheduler

Votre question a révélé un vrai piège : `check_and_execute_commands()` et
`retry_procedure()` appelaient `get_current_session()` **à chaque appel**
plutôt qu'une fois au démarrage. Scénario concret que vous décriviez -
démarrer le scheduler sur l'appareil A, puis basculer le profil actif de
l'UI vers B pendant que A tourne encore - aurait fait migrer
silencieusement la prochaine commande planifiée de A vers B, alors que la
connexion socket de A restait, elle, bien active en arrière-plan (les
deux niveaux ne réagissent pas pareil au changement de profil).

**Corrigé** : `check_and_execute_commands(..., session=None)` et
`retry_procedure(..., session=None)` acceptent maintenant une session
explicite (repli sur `get_current_session()` seulement si non fournie -
compat CLI inchangée). `run_scheduler()` dans l'UI capture
`scheduler_session = get_current_session()` **une seule fois** au
démarrage du scheduler, et transmet ce même objet à chaque itération de
sa boucle (`start_STA_connection`, `check_and_execute_commands`) -
indépendant de tout changement ultérieur du profil actif dans l'UI.

Testé : scheduler démarré sur `DWARF3_3AD246`, bascule UI vers `Mini`
pendant l'exécution, `check_and_execute_commands(session=scheduler_session)`
continue bien de cibler `DWARF3_3AD246` - confirmé que sans ce fix, l'appel
aurait basculé vers `Mini`.

**Réponse à votre question** : au niveau connexion, oui, la première
reste active en arrière-plan quel que soit le profil affiché dans l'UI.
Au niveau scheduler, maintenant aussi oui (grâce à ce fix) - à condition
que chaque scheduler démarré capture sa session au lancement, ce qui est
désormais le cas pour `run_scheduler()`.

## Bug BLE réel : `set_disconnected_callback` retiré de `bleak` moderne (fait, testé)

Erreur rencontrée en test réel : `'BleakClient' object has no attribute
'set_disconnected_callback'`. Cette méthode a été retirée des versions
récentes de `bleak` (confirmé sur `bleak 3.0.2`) au profit du paramètre
`disconnected_callback=` au constructeur. Le callback `onDisconnected`
défini dans `dwarf_lib_ble.py` n'était de toute façon jamais réellement
branché (aucun appel `set_disconnected_callback(onDisconnected)`
n'existe ailleurs dans le fichier) - cette ligne, dans `action_disconnect`,
ne servait qu'à nettoyer un callback jamais enregistré.

**Corrigé** : appel protégé par `hasattr()`, compatible avec toutes les
versions de `bleak` (ancienne ou moderne), sans changement de
comportement sinon.

## Bug UI réel : sélecteur de profil verrouillé après connexion BLE (fait)

Symptôme rencontré en test : impossible de connecter un second Dwarf.
Cause trouvée : `start_bluetooth()` appelle `self.disable_controls()`
(verrouille `config_combobox`, le sélecteur de profil) au démarrage de la
connexion, mais `bluetooth_connect_thread()` ne rappelait **jamais**
`self.enable_controls()` à la fin - ni en cas de succès, ni en cas
d'échec. Le sélecteur restait donc verrouillé indéfiniment après la
première connexion BLE réussie, empêchant de basculer vers un autre
profil pour en connecter un second (le chemin `run_scheduler`, lui,
réactivait déjà correctement les contrôles à plusieurs points de sortie -
seul le thread de connexion pure oubliait de le faire).

**Corrigé** : `enable_controls()` déplacé dans un bloc `finally`, appelé
systématiquement quelle que soit l'issue de la tentative de connexion.

Sans rapport avec le multi-dwarf en soi, mais bloquait directement le
scénario de test que vous décriviez.

## Correctif import cassé + `run_toogle_lights` session-aware (fait, testé)

`astro_dwarf_session_UI.py` importait encore `perform_getstatus` depuis
`dwarf_utils` (déplacée vers `dwarf_utilsV2.py` - import cassé,
`ImportError` au chargement) et `get_client_status` depuis
`websockets_utils` (version globale, non session-aware). Imports corrigés
selon votre correction.

`get_client_status` de `dwarf_session_socket.py` exige `session` en
paramètre obligatoire (pas de valeur par défaut) - `run_toogle_lights()`
mise à jour pour capturer `session = get_current_session()` et le passer
à `get_client_status(session)` ainsi qu'à `perform_powerCloseRGB`/
`perform_powerOpenRGB`/`perform_powerIndOff`/`perform_powerIndOn`. Garde
ajoutée pour un message d'erreur clair si aucune session active
("connect a Dwarf first") plutôt qu'un plantage confus sur
`NoneType.client_instance`.

Testé : statut RGB/power lu depuis la session, puis les 2 actions de
bascule routées correctement vers cette même session.

## Sélecteur de profil encore bloqué : le chemin scheduler manquait aussi

Le fix précédent (BLE) ne suffisait pas : `start_scheduler()` verrouille
aussi `config_combobox` au clic, et ne le libérait qu'à l'arrêt complet
du scheduler (`stop_scheduler`'s `finalize_stop()`). Avant le fix de
session figée, c'était logique (un seul appareil géré à la fois) - mais
maintenant que `run_scheduler()` fige sa session dès le démarrage, changer
de profil pendant qu'un scheduler tourne pour un autre appareil ne
l'affecte plus du tout. Le verrou n'avait donc plus lieu d'être pendant
toute la durée du scheduler.

**Corrigé** : `self.enable_controls()` appelé juste après la capture de
`scheduler_session` dans `run_scheduler()` - le sélecteur se débloque dès
que la session est figée, permettant de basculer vers un autre profil et
connecter/piloter un second Dwarf pendant que le premier scheduler tourne
toujours en arrière-plan.

## Bug d'import réel : `disconnect_socket_session` non défini (fait, testé)

Erreur rencontrée : `name 'disconnect_socket_session' is not defined`.
Cause : `from .dwarf_session_socket import disconnect_socket` (sans alias)
écrasait silencieusement l'import du `disconnect_socket` global
(`websockets_utils`, ligne 4) dans l'espace de noms du module - **et**
laissait `disconnect_socket_session` (utilisé dans `perform_disconnect`
et `resolve_dwarf_ip`) totalement non défini, puisque cet alias n'avait
jamais été créé.

**Corrigé** : `from .dwarf_session_socket import disconnect_socket as
disconnect_socket_session` - alias explicite, comme pour
`connect_socket_session`/`get_camera_param_v3_session`/`get_client_status_session`
juste à côté.

Testé : `perform_disconnect(session=s)` route bien vers
`disconnect_socket_session`, `perform_disconnect()` (sans session) route
bien vers le `disconnect_socket` global - les deux chemins désormais
correctement distincts.

## Bouton scheduler bloqué entre profils : fix minimal (fait)

Confirmé par votre test : le bouton "Start Scheduler" est piloté par un
état unique (`self.scheduler_running`) sur toute l'UI, pas par profil.
Une fois lancé pour A, basculer vers B affiche "Stop Scheduler" alors que
B n'a jamais démarré - impossible de lancer B, et si on avait cliqué
quand même, ça aurait risqué d'arrêter A par erreur.

**Choix retenu** (option prudente) : toujours **un seul scheduler à la
fois** pour l'instant - pas de vraie exécution concurrente de deux
schedulers. Mais l'UI devient honnête à ce sujet :
- `self.scheduler_running_config_name` mémorise quel profil possède le
  scheduler actif.
- `start_scheduler()`/`toggle_scheduler()` détectent qu'on tente
  d'agir depuis un **autre** profil que celui qui tourne, et affichent un
  message clair (`messagebox.showwarning`) au lieu de démarrer un second
  scheduler ou d'arrêter le mauvais.
- `on_combobox_change()` rafraîchit maintenant l'affichage du bouton
  (`refresh_scheduler_button()`) pour refléter l'état du profil
  sélectionné, pas celui qui tourne ailleurs.
- Revenir sur le profil qui tourne réellement permet de l'arrêter
  normalement.

**Non traité, noté pour plus tard** : le thread de
`run_stop_astro_photo` (`perform_stopAstroPhoto` sans `session=`) cible
toujours la session globale par défaut, pas forcément le bon appareil en
contexte multi-profil - repéré en marge de ce fix, hors périmètre choisi.

**Refonte complète (exécution concurrente réelle de 2-4 schedulers)**
reste à faire si vous en avez besoin plus tard - actuellement, seule la
couche session (`dwarf_python_api`) le supporte déjà ; la couche UI/
scheduler d'`astro_dwarf_session` nécessiterait le même traitement
"état par profil" appliqué ici au bouton, mais étendu à tout le
sous-système (`scheduler_thread`, `scheduler_stop_event`, `run_scheduler`).

## "Scheduler 2" : second bouton/thread indépendant pour tester le parallélisme réel

Exactement votre proposition : plutôt qu'une refonte générale par profil
(qui toucherait `toggle_buttons`/`session_info_label`/tous les contrôles
caméra partagés), duplication ciblée du **seul** mécanisme qui doit
vraiment tourner en tâche de fond : le scheduler.

- `self.scheduler_running_2`, `self.scheduler_stop_event_2`,
  `self.scheduler_running_config_name_2` - état totalement indépendant du
  scheduler principal, pas de garde-fou entre les deux (c'est tout
  l'intérêt).
- Bouton **"Start Scheduler 2"** ajouté à côté du premier.
- `start_scheduler_2()` capture `get_current_session()` **au moment du
  clic** - même mécanisme de figeage que le scheduler principal. Donc :
  sélectionner le profil B dans la combo existante, cliquer "Start
  Scheduler 2", puis revenir sur A sans rien perturber.
- `run_scheduler_2()` : boucle allégée volontairement - ne touche pas
  `toggle_buttons`/`session_info_label`/les boutons caméra (qui restent
  liés au profil actuellement affiché). Juste `start_STA_connection` +
  boucle `check_and_execute_commands`, avec logs préfixés `[Scheduler 2]`.
- Arrêt propre à la fermeture de l'app ajouté aussi pour ce second thread.

**Assumé/à savoir** : ceci est un harnais de test volontairement minimal,
pas une fonctionnalité polie - pas d'affichage de statut dédié pour le
slot 2, pas de bouton d'arrêt de session astro dédié, etc. Si l'usage à
deux schedulers devient permanent plutôt qu'un test, ça vaudra le coup de
revenir vers la vraie refonte par profil évoquée précédemment.

Testé : le mécanisme de figeage (chaque slot capture une session distincte
au moment du clic, indépendamment de ce que montre la combo ensuite) est
validé. La boucle `run_scheduler_2` elle-même (thread + vraie fenêtre
Tkinter) n'a pas pu être testée dans ce sandbox - pas d'environnement
graphique disponible ici.

## Logging en parallèle : le handler de fichier global aurait perdu des données

Votre question a révélé un vrai problème pour le test à 2 schedulers.
`my_logger.py` utilise un **unique handler de fichier global**, redirigé à
chaque `setup_new_config()` (donc à chaque changement de profil dans la
combo). Ça marche très bien en usage séquentiel (votre test précédent),
mais avec deux schedulers **vraiment** en parallèle : sélectionner Mini
pour cliquer "Start Scheduler 2" bascule ce handler global sur le fichier
de Mini - et à partir de là, **le scheduler 1 (Default) arrête
silencieusement d'écrire dans son propre fichier**, ses logs partant dans
celui de Mini à la place.

**Corrigé** : `start_scheduler_2()` crée maintenant son **propre**
`FileHandler` dédié, pointé sur le fichier de log de sa session au moment
du pin, complètement indépendant du handler global - reste attaché tout
le long de sa vie, peu importe ce que fait la combo ensuite. Nettoyé
proprement à l'arrêt (`run_scheduler_2`'s `finally`) et à la fermeture de
l'app.

Testé : simulation avec handler global + handler dédié scheduler 2,
confirmé que le fichier dédié reçoit bien tous les messages même après
que le handler global ait basculé ailleurs.

**Limite restante, cosmétique seulement** (pas de perte de données) : la
fenêtre de log UI reste un widget unique partagé - les messages détaillés
du scheduler 2 (goto, capture...) n'y apparaîtront que si le scheduler 1
est démarré (son `start_logHandler()` attache le `TextHandler` global),
et y seront mélangés sans étiquette avec ceux du scheduler 1. Seules mes
lignes `[Scheduler 2]` explicites resteront clairement identifiables à
l'écran. Pas traité pour l'instant (harnais de test, cosmétique).

## Deux bugs bloquants au lancement (fait)

1. **`get_current_config_name` non importé** : utilisée dans
   `_scheduler_running_for_current_profile()`/`refresh_scheduler_button()`
   ajoutées précédemment, mais oubliée dans l'import
   `from astro_dwarf_scheduler import ...`. Corrigé.
2. **`self.session_running` non initialisé** : bug préexistant, pas lié à
   mes changements - seulement défini à l'intérieur de `run_scheduler()`,
   jamais dans `__init__`. Si `update_session_info()` (rafraîchissement
   périodique) tourne avant le tout premier démarrage du scheduler,
   `AttributeError`. Corrigé : initialisé dans `__init__` aux côtés des
   autres états scheduler.

## Bug critique découvert par votre test : `motor_action` jamais migrée (fait, testé)

Votre test de positionnement polaire a révélé le trou le plus important à
ce jour : `motor_action()` (utilisée par le positionnement polaire, 12
branches selon l'action demandée) **n'avait jamais été migrée** -
totalement oubliée dans tout le travail précédent. Résultat exact que
vous décriviez : le log changeait bien de fichier en changeant de combo,
mais les commandes réelles continuaient d'aller au dernier appareil
connecté (Mini, devenu "session par défaut" du gestionnaire), quel que
soit le profil affiché.

**Corrigé** : les 12 branches de `motor_action()` routent maintenant vers
`session` si fournie. Toutes les fonctions UI qui l'appellent (et
d'autres oubliées au passage) mises à jour pour capturer
`session = get_current_session()` et le propager :
- `run_start_polar_position` (le bouton que vous testiez) - utilise aussi
  maintenant `session.config.dwarf_model_id` au lieu de la config globale
  pour déterminer D3 vs Mini (positions moteur différentes selon le
  modèle).
- `run_unset_lock_device`, `run_start_eq_solving`, `start_auto_focus`,
  `run_start_calibration`, `run_stop_astrophotos`, `run_stop_astro_photo`,
  `run_start_powerdown`, `run_start_reboot` - même correction.

Testé : avec Mini comme session par défaut du gestionnaire (donc
exactement votre scénario), sélectionner explicitement D3 dans la combo
et lancer `motor_action` route bien 100% des commandes vers D3, plus
aucune fuite vers Mini.

**Pourquoi ça a échappé à la vérification précédente** : cette fonction
utilise un système de branches `if action == N` très différent des autres
(`perform_*`), et n'avait jamais été identifiée dans les greps successifs
qui cherchaient spécifiquement `^def perform_`.

## Bug BLE réel : "Cancel" piégé dans une boucle "Please enter a valid number" (fait, testé)

Dans l'écran de sélection d'appareil (plusieurs Dwarf détectés en BLE),
`simpledialog.askinteger()` retourne `None` aussi bien en cliquant
**Annuler** qu'en fermant la fenêtre - mais le code traitait ce `None`
exactement comme une saisie invalide, réaffichait l'erreur et reposait la
question indéfiniment. Impossible d'annuler.

**Corrigé** : distinction explicite entre "Cancel/fenêtre fermée" (`None`
→ sortie propre, comme sélectionner 0) et "saisie hors bornes" (nombre
valide mais `< 0` ou `> nb d'appareils` → message d'erreur + redemande,
comportement normal conservé).

Testé sur les 3 cas (Cancel, hors bornes, valide) - Cancel ferme
maintenant proprement au lieu de boucler.

**Note (pas un bug)** : l'absence d'étoile visible en test EQ Solving
indoor est une contrainte physique normale (plate-solving a besoin d'un
vrai champ stellaire), pas un problème multi-dwarf.

## Vrai filtre de log par session (fait, testé)

Fini le bricolage "handler dédié qui capture quand même tout" - un vrai
filtre cette fois. Chaque `logging.LogRecord` porte déjà gratuitement
`record.thread` (l'identifiant du thread émetteur) - et comme chaque
scheduler tourne dans son propre thread, un `logging.Filter` basé sur
cet identifiant sépare parfaitement les deux flux, **sans toucher à aucun
appel `log.notice(...)`/`log.info(...)` existant** dans tout le code.

- `_ThreadFilter` (nouvelle classe) + `_attach_dedicated_log_file()`
  (helper commun) : créent un `FileHandler` + filtre restreint à un
  `thread_ident` précis.
- **`run_scheduler()` (scheduler principal)** reçoit maintenant aussi son
  propre fichier dédié filtré - avant, seul le scheduler 2 en avait un
  (et même celui-là n'était pas vraiment filtré, juste dupliqué). Les
  deux fichiers sont maintenant symétriques et propres.
- `run_scheduler_2()` : la logique d'attache du handler déplacée de
  `start_scheduler_2()` vers le début de `run_scheduler_2()` elle-même -
  nécessaire car `Thread.ident` n'existe qu'une fois le thread réellement
  démarré, pas avant.
- Corrigé au passage : `perform_disconnect()` dans le `finally` de
  `run_scheduler()` ne passait pas `session=` - déconnectait la mauvaise
  session en fin de run.

Testé (2 threads réels, écriture simultanée) : chaque fichier ne contient
**que** ses propres messages, aucune trace croisée même en exécution
vraiment parallèle - contrairement au filtre précédent basé sur "premier
arrivé, premier servi" entre handler global et dédié.

**Fenêtre de log affichée** : toujours partagée/mélangée pour l'instant -
pas traité ici (le même principe de filtre par thread s'appliquerait au
`TextHandler`, mais vous avez demandé le filtre fichier en priorité).
Dites-moi si vous voulez aussi ce traitement pour la fenêtre.

## Résidu éliminé : le handler global exclut maintenant les threads déjà dédiés (fait, testé)

Confirmé : le souci résiduel (5/1 lignes croisées) venait bien
d'`update_log_file()` - son `FileHandler` global n'avait aucun filtre, donc
peu importe vers quel fichier il pointait, il captait tout le trafic du
logger racine, y compris les threads scheduler ayant pourtant déjà leur
propre fichier dédié filtré.

**Corrigé proprement, en respectant les couches** : `dwarf_python_api`
(bas niveau) ne connaît rien à la notion UI de "scheduler" - il expose
juste un mécanisme générique d'exclusion par thread :
- `my_logger.py` : `exclude_thread_from_shared_log(ident)` /
  `include_thread_in_shared_log(ident)` + `_SharedLogThreadFilter` attaché
  au `file_handler` global dans `update_log_file()`.
- `astro_dwarf_session_UI.py` : `_attach_dedicated_log_file()` appelle
  désormais `exclude_thread_from_shared_log()` en plus de créer son
  handler dédié ; nouveau `_detach_dedicated_log_file()` fait l'inverse à
  l'arrêt. `run_scheduler()`/`run_scheduler_2()` mis à jour pour utiliser
  ces helpers symétriques.

Testé : un thread avec son propre handler dédié est bien exclu du fichier
global une fois enregistré, tout en laissant le thread principal (et tout
thread non-dédié) continuer d'y écrire normalement.

Avec ce fix, les fichiers de log de chaque appareil devraient être
complètement propres, y compris pendant l'exécution vraiment parallèle des
deux schedulers.

## Dernier résidu fermé : thread `event_loop` de chaque session (fait, testé)

Les 4 lignes DEBUG restantes (`WebSocket Client Send Start/End`) venaient
du thread d'arrière-plan asyncio propre à chaque session
(`session.event_loop_thread`, dans `dwarf_session_socket.py`) - distinct
du thread "scheduler" que j'excluais déjà. Ce thread gère l'I/O socket bas
niveau, créé paresseusement à la première connexion (et potentiellement
recréé lors d'une reconnexion).

**Corrigé** : `_ensure_session_io_thread_excluded()` (nouvelle méthode),
appelée juste après connexion et à chaque itération de boucle des deux
schedulers (idempotente - ne réenregistre rien si déjà exclu, donc
aucun coût même appelée en boucle) - détecte et exclut ce thread dès
qu'il existe, y compris après une reconnexion qui en recrée un nouveau.
Tous les threads exclus par un run sont réintégrés au nettoyage final.

Testé : idempotence confirmée (appels répétés = un seul enregistrement
réel).

**Explication du `.old`** (pas un bug) : comportement préexistant
d'`update_log_file()` - à chaque fois qu'un profil déjà utilisé plus tôt
dans le même run est resélectionné, son fichier contient déjà du contenu
sur disque, qui est déplacé vers `.old` avant de repartir sur un fichier
neuf. D'où le contenu d'un même appareil parfois fragmenté entre `.log`
et `.log.old` au fil des changements de profil.

## Audit systématique côté `astro_dwarf_session` (fait, testé)

Suite à `motor_action`, audit exhaustif : liste des 110 fonctions
session-aware de `dwarf_utils.py`, recherche de chaque appel dans
`dwarf_session.py`/`astro_dwarf_scheduler.py`/`astro_dwarf_session_UI.py`
sans `session=`. **6 vrais oublis trouvés et corrigés** :

- `astro_dwarf_scheduler.py` : `perform_read_camera_params_http_v3` (dans
  `check_and_execute_commands`, pour les settings caméra du mail de fin de
  session), `read_bluetooth_ble_psd`/`_STA_ssid`/`_STA_pwd`,
  `perform_time`/`perform_timezone`/`perform_set_location` (dans
  `start_connection`).
- `astro_dwarf_session_UI.py` : `finalize_close()` ne déconnectait
  qu'**une seule** session à la fermeture de l'app - corrigé pour
  déconnecter **toutes** les sessions connues via `get_manager().all()`.
  `verifyCountdown()`'s chemin de timeout forcé utilisait aussi
  `perform_disconnect()` sans session - la session figée du scheduler
  principal est maintenant aussi gardée en attribut d'instance
  (`self.scheduler_session`) pour que ce chemin y accède correctement.

**2 faux positifs écartés** après vérification : `get_client_status(session)`
(appel positionnel déjà correct) et les 3 appels dans le bloc
`if __name__ == '__main__':` de `astro_dwarf_scheduler.py` (CLI autonome,
mono-dwarf par nature, décision déjà actée).

Testé : `finalize_close()` déconnecte bien les deux appareils simulés, pas
un seul.

## Étapes suivantes suggérées

- **Écran de contrôle multi-session (UI, à venir)** : combo/sélecteur de
  session en cours (peuplé via `get_manager().all()`, aucun changement
  côté `dwarf_python_api` nécessaire pour ça) ; bascule d'affichage vers
  la session choisie sans interrompre les autres ; à terme, un écran
  découpé en 2-4 panneaux (un par session active), chacun affichant son
  propre `get_client_status(session)` - déjà isolé par session côté cache
  (`previous_values`), donc pas de risque de mélange entre panneaux. En
  en-tête, afficher l'étape en cours (`step_1a`, `step_2`, etc. déjà
  logués dans `start_dwarf_session`) plutôt que de faire défiler les logs.

1. Fusionner ces 3 fichiers sur `multi_V3` tels quels (zéro risque, rien
   d'existant n'est modifié).
2. Créer deux `DwarfConfig` réels (un pour le Mini, un pour le D3) et un
   `DwarfManager`, les garder de côté dans un petit script de test
   (`test_multi_v3.py`) qui ouvre les deux connexions et fait un
   `get_client_status()` sur chacune, sans encore toucher `dwarf_utils.py`.
3. Migrer `perform_goto`, `perform_takeAstroPhoto`,
   `perform_waitEndAstroPhoto` (le trio le plus utilisé par
   `astro_dwarf_session`) selon le patron ci-dessus, testé sur les deux
   appareils.
4. Étendre progressivement aux autres `perform_*`.
5. Migrer les fonctions `read_*`/`config.ini` de la même manière, en leur
   passant `session.config` au lieu de relire le fichier à chaque appel.
6. Une fois `dwarf_utils.py` entièrement migré, adapter `astro_dwarf_session`
   pour créer un `DwarfManager` et indexer ses sessions de planification par
   `dwarf_uid`.
7. Retirer `get_default_session()` / le mode compat une fois plus aucun
   appelant ne dépend du mono-dwarf implicite.
