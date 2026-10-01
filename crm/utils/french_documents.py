"""French versions of the read-only help and legal documents."""

from datetime import datetime


HELP = """
<html><body style="font-family: 'Segoe UI', Arial, sans-serif; color:#334155; line-height:1.8; margin:20px;">
<h1>📖 Guide d'utilisation</h1>
<p>DigiSpher EMR est un dossier médical électronique pour les médecins exerçant seuls et les petits cabinets. Il permet de gérer les patients, rendez-vous, notes cliniques, allergies, constantes, ordonnances et finances.</p>
<h2>Sommaire</h2>
<ol><li><a href="#start">Premiers pas et connexion</a></li><li><a href="#patients">Patients</a></li><li><a href="#appointments">Rendez-vous</a></li><li><a href="#notes">Notes cliniques</a></li><li><a href="#allergies">Allergies et constantes</a></li><li><a href="#prescriptions">Ordonnances</a></li><li><a href="#settings">Paramètres et sécurité</a></li><li><a href="#backup">Sauvegardes</a></li><li><a href="#tips">Bonnes pratiques et dépannage</a></li></ol>
<h2 id="start">🏥 Premiers pas et connexion</h2>
<p>Connectez-vous avec vos identifiants. Lors de la première connexion, changez immédiatement votre mot de passe. En cas d'oubli, choisissez « Mot de passe oublié ? », saisissez votre nom d'utilisateur, confirmez le nom du cabinet puis définissez deux fois un nouveau mot de passe. Le nom du cabinet doit correspondre à celui enregistré ; la comparaison ne tient pas compte des majuscules.</p>
<h2 id="patients">👥 Gestion des patients</h2>
<p>Dans « Patients », choisissez « Ajouter un patient ». Le prénom et le nom sont obligatoires. Renseignez si possible la date de naissance, le genre, les coordonnées, les antécédents médicaux et le contact d'urgence, puis enregistrez. Sélectionnez une ligne pour modifier le dossier. Vérifiez soigneusement le patient avant toute suppression : les rendez-vous et notes associés peuvent également être supprimés.</p>
<h2 id="appointments">📅 Rendez-vous</h2>
<p>Dans « Rendez-vous », créez une consultation, sélectionnez le patient, la date, l'heure, le médecin et le motif. Les statuts possibles sont : planifié, confirmé, en cours, terminé, annulé et absent. Sélectionnez un rendez-vous puis « Modifier » pour le reporter ou changer son statut.</p>
<h2 id="notes">📝 Notes cliniques SOAP</h2>
<p>Dans « Notes cliniques », créez une note, sélectionnez le patient et renseignez les quatre rubriques SOAP : Subjectif (symptômes rapportés), Objectif (examen et constantes), Évaluation (diagnostic) et Plan (traitement et suivi). Le contexte du patient affiche les allergies actives et les dernières constantes. Vous pouvez consulter les notes d'un patient et les exporter en PDF.</p>
<p><strong>Signature :</strong> « Finaliser et signer » verrouille définitivement la note en lecture seule. Vérifiez son contenu avant de confirmer.</p>
<h2 id="allergies">⚠️ Allergies et constantes</h2>
<p>Dans le dossier du patient, ajoutez les allergies avec l'allergène, la réaction, la gravité, la date d'apparition et des notes. Les allergies graves font apparaître des alertes bien visibles.</p>
<p>Enregistrez les constantes : pression artérielle, fréquence cardiaque, température, poids, taille, saturation en oxygène et fréquence respiratoire. L'IMC est calculé automatiquement lorsque le poids et la taille sont présents. Une couleur signale si l'IMC est dans la plage habituelle de 18,5 à 24,9.</p>
<h2 id="prescriptions">💊 Ordonnances</h2>
<p>Dans « Ordonnances », choisissez un patient et ajoutez un ou plusieurs médicaments. Pour chacun, indiquez le nom, la posologie, la fréquence et la durée. Ajoutez les instructions destinées au patient et le nom du prescripteur. Enregistrez puis exportez le document en PDF ; il comprend les coordonnées du patient et du cabinet, les médicaments, la date et le numéro de l'ordonnance.</p>
<h2 id="settings">⚙️ Paramètres, profil et sécurité</h2>
<p>Dans « Paramètres », modifiez les informations du cabinet : nom officiel, adresse complète et numéro de licence. Ces informations apparaissent sur les documents exportés et le nom du cabinet sert à la récupération du mot de passe. Modifiez votre profil et votre mot de passe depuis « Modifier le profil ». Laissez les champs du nouveau mot de passe vides pour conserver l'actuel.</p>
<p>Choisissez la langue de l'interface dans « Paramètres ». Enregistrez régulièrement votre travail : une période d'inactivité entraîne une déconnexion automatique et les modifications non enregistrées seront perdues.</p>
<h2 id="backup">💾 Sauvegarde de la base de données</h2>
<p>Dans « Paramètres », choisissez « Sauvegarder », puis un emplacement sûr pour le fichier horodaté. Pour un cabinet actif, effectuez une sauvegarde quotidienne ; pour un cabinet moins actif, une sauvegarde hebdomadaire peut convenir. Sauvegardez également avant toute mise à jour importante. Conservez une copie sur un support distinct et protégé.</p>
<h2 id="tips">💡 Bonnes pratiques et dépannage</h2>
<ul><li>Saisissez les notes rapidement après chaque consultation ; utilisez des termes et abréviations cohérents.</li><li>Vérifiez l'identité, les allergies et les coordonnées du patient avant d'enregistrer.</li><li>Utilisez un mot de passe robuste et ne partagez pas vos identifiants. Déconnectez-vous en quittant votre poste.</li><li>Si la connexion échoue, utilisez le lien de réinitialisation sur l'écran de connexion.</li><li>Si la base de données est verrouillée, vérifiez qu'une seule instance de l'application est ouverte.</li><li>Si des données semblent manquer, vérifiez les filtres et la période affichée avant de restaurer une sauvegarde.</li></ul>
<p>Pour une assistance technique, une demande de fonctionnalité ou un signalement de problème, contactez votre administrateur informatique ou l'équipe DigiSpher.</p>
<p><small>Version 2.0.0 (édition pour cabinet individuel) • Mise à jour : septembre 2026</small></p>
</body></html>
"""


def privacy_html():
    return f"""<html><body style="font-family:'Segoe UI',Arial,sans-serif;color:#334155;line-height:1.6;">
    <h2>1. Logiciel installé localement</h2>
    <p>DigiSpher EMR est une <strong>solution installée localement</strong>. Le logiciel et toutes les données associées sont installés, conservés et traités sur votre propre matériel.</p>
    <h2>2. Propriété et stockage des données</h2>
    <p>Contrairement aux solutions infonuagiques, DigiSpher EMR ne stocke, ne transmet ni ne sauvegarde vos données sur des serveurs externes. Les dossiers des patients, les notes cliniques et les antécédents médicaux sont conservés dans une base SQLite locale sur cet ordinateur.</p>
    <h2>3. Responsabilité de l'utilisateur</h2>
    <p>En tant qu'utilisateur et administrateur de cette installation, vous reconnaissez et acceptez les responsabilités suivantes :</p>
    <ul><li><strong>Sécurité des données :</strong> vous êtes seul responsable de la protection des accès physiques et numériques à l'ordinateur utilisé.</li>
    <li><strong>Sauvegardes :</strong> vous devez effectuer régulièrement des sauvegardes de la base de données. Un outil est disponible dans les paramètres, mais vous devez lancer la sauvegarde.</li>
    <li><strong>Prévention des pertes :</strong> DigiSpher EMR Systems ne peut pas récupérer les données perdues à la suite d'une panne matérielle, d'un vol ou d'une suppression accidentelle, car aucune copie n'est conservée par l'éditeur.</li></ul>
    <h2>4. Conformité</h2>
    <p>Vous devez vous assurer que l'utilisation du logiciel et le stockage des données des patients respectent les règles de confidentialité locales, régionales et nationales applicables (par exemple HIPAA ou RGPD). Vous devez notamment protéger l'appareil par chiffrement et par mot de passe.</p>
    <p style="color:#94A3B8;border-top:1px solid #E2E8F0;padding-top:20px;">Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y')} | DigiSpher EMR Systems</p>
    </body></html>"""


LICENSE = """<html><body style="font-family:'Segoe UI',Arial,sans-serif;color:#334155;line-height:1.6;">
<p style="background:#FEF2F2;padding:15px;"><strong>AVIS JURIDIQUE IMPORTANT :</strong> ce logiciel est concédé sous licence et non vendu. Son utilisation vaut acceptation des conditions ci-dessous.</p>
<h2>1. Octroi de licence</h2><p>DigiSpher EMR Systems vous accorde une licence limitée, révocable, non exclusive et non transférable pour utiliser DigiSpher EMR conformément au présent contrat.</p>
<h2>2. Type de licence : cabinet individuel commercial</h2><p>Cette licence commerciale est destinée à un cabinet individuel. Elle autorise un seul (1) médecin ou professionnel de santé à utiliser le logiciel.</p>
<h2>3. Restrictions d'installation et d'utilisation</h2><ul><li><strong>Un seul ordinateur :</strong> la licence autorise l'installation et l'utilisation sur une seule (1) machine physique ou un seul poste de travail.</li><li><strong>Aucun partage réseau :</strong> le logiciel ne peut pas être installé sur un serveur pour être utilisé depuis plusieurs postes ou par plusieurs utilisateurs.</li><li><strong>Licence non transférable :</strong> vous ne pouvez ni louer, prêter, vendre, redistribuer ni concéder en sous-licence ce logiciel.</li></ul>
<h2>4. Partage non autorisé et conséquences juridiques</h2><p>La distribution, la copie ou le partage du logiciel avec d'autres professionnels, cabinets ou tiers constitue une violation du présent contrat et des lois internationales sur le droit d'auteur.</p><p><strong>Avertissement :</strong> toute utilisation ou distribution non autorisée entraîne la résiliation immédiate de la licence et peut donner lieu à des sanctions civiles et pénales, notamment des dommages-intérêts pour violation du droit d'auteur.</p>
<h2>5. Limitation de responsabilité</h2><p>DigiSpher EMR Systems ne saurait être tenu responsable de dommages, notamment de pertes de bénéfices, d'interruptions d'activité ou de pertes d'informations, résultant de l'utilisation du produit par les utilisateurs autorisés ou de leur incapacité à l'utiliser.</p>
<p style="color:#94A3B8;border-top:1px solid #E2E8F0;padding-top:20px;">Identifiant de licence : SPEC-2024-SOLO-001 | © 2024 DigiSpher EMR Systems</p>
</body></html>"""
