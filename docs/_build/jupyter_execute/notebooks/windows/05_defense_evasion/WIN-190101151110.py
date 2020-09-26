# Active Directory Replication User Backdoor

## Metadata


|                   |    |
|:------------------|:---|
| collaborators     | ['Roberto Rodriguez @Cyb3rWard0g', 'Jose Rodriguez @Cyb3rPandaH'] |
| creation date     | 2019/01/01 |
| modification date | 2020/09/20 |
| playbook related  | ['WIN-180815210510'] |

## Hypothesis
Adversaries with enough permissions (domain admin) might be adding an ACL to the Root Domain for any user to abuse active directory replication services.

## Technical Context
Active Directory replication is the process by which the changes that originate on one domain controller are automatically transferred to other domain controllers that store the same data.
Active Directory data takes the form of objects that have properties, or attributes.
Each object is an instance of an object class, and object classes and their respective attributes are defined in the Active Directory schema. The values of the attributes define the object, and a change to a value of an attribute must be transferred from the domain controller on which it occurs to every other domain controller that stores a replica of that object.

## Offensive Tradecraft
An adversary with enough permissions (domain admin) can add an ACL to the Root Domain for any user, despite being in no privileged groups, having no malicious sidHistory, and not having local admin rights on the domain controller. This is done to bypass detection rules looking for Domain Admins or the DC machine accounts performing active directory replication requests against a domain controller.

The following access rights / permissions are needed for the replication request according to the domain functional level

| Control access right symbol | Identifying GUID used in ACE |
| :-----------------------------| :------------------------------|
| DS-Replication-Get-Changes | 1131f6aa-9c07-11d1-f79f-00c04fc2dcd2 |
| DS-Replication-Get-Changes-All | 1131f6ad-9c07-11d1-f79f-00c04fc2dcd2 |
| DS-Replication-Get-Changes-In-Filtered-Set | 89e95b76-444d-4c62-991a-0facbeda640c |

Additional reading
* https://github.com/OTRF/ThreatHunter-Playbook/tree/master/docs/library/active_directory_replication.md

## Mordor Test Data


|           |           |
|:----------|:----------|
| metadata  | https://mordordatasets.com/notebooks/small/windows/05_defense_evasion/SDWIN-190301125905.html        |
| link      | [https://raw.githubusercontent.com/OTRF/mordor/master/datasets/small/windows/defense_evasion/host/empire_powerview_ldap_ntsecuritydescriptor.zip](https://raw.githubusercontent.com/OTRF/mordor/master/datasets/small/windows/defense_evasion/host/empire_powerview_ldap_ntsecuritydescriptor.zip)  |

## Analytics

### Initialize Analytics Engine

from openhunt.mordorutils import *
spark = get_spark()

### Download & Process Mordor Dataset

mordor_file = "https://raw.githubusercontent.com/OTRF/mordor/master/datasets/small/windows/defense_evasion/host/empire_powerview_ldap_ntsecuritydescriptor.zip"
registerMordorSQLTable(spark, mordor_file, "mordorTable")

### Analytic I
Look for any user accessing directory service objects with replication permissions GUIDs


| Data source | Event Provider | Relationship | Event |
|:------------|:---------------|--------------|-------|
| Windows active directory | Microsoft-Windows-Security-Auditing | User accessed AD Object | 4662 |

df = spark.sql(
'''
SELECT `@timestamp`, Hostname, SubjectUserName, ObjectName, OperationType
FROM mordorTable
WHERE LOWER(Channel) = "security"
    AND EventID = 4662
    AND ObjectServer = "DS"
    AND AccessMask = "0x40000"
    AND ObjectType LIKE "%19195a5b_6da0_11d0_afd3_00c04fd930c9%"
'''
)
df.show(10,False)

### Analytic II
Look for any user modifying directory service objects with replication permissions GUIDs


| Data source | Event Provider | Relationship | Event |
|:------------|:---------------|--------------|-------|
| Windows active directory | Microsoft-Windows-Security-Auditing | User modified AD Object | 5136 |

df = spark.sql(
'''
SELECT `@timestamp`, Hostname, SubjectUserName, ObjectDN, AttributeLDAPDisplayName
FROM mordorTable
WHERE LOWER(Channel) = "security"
    AND EventID = 5136
    AND lower(AttributeLDAPDisplayName) = "ntsecuritydescriptor"
    AND (AttributeValue LIKE "%1131f6aa_9c07_11d1_f79f_00c04fc2dcd2%"
        OR AttributeValue LIKE "%1131f6ad_9c07_11d1_f79f_00c04fc2dcd2%"
        OR AttributeValue LIKE "%89e95b76_444d_4c62_991a_0facbeda640c%")
'''
)
df.show(10,False)

## Known Bypasses


| Idea | Playbook |
|:-----|:---------|

## False Positives
None

## Hunter Notes
None

## Hunt Output

| Type | Link |
| :----| :----|
| Sigma Rule | [https://github.com/OTRF/ThreatHunter-Playbook/blob/master/signatures/sigma/win_ad_object_writedac_access.yml](https://github.com/OTRF/ThreatHunter-Playbook/blob/master/signatures/sigma/win_ad_object_writedac_access.yml) |
| Sigma Rule | [https://github.com/Cyb3rWard0g/ThreatHunter-Playbook/tree/master/signatures/sigma/win_ad_replication_user_backdoor.yml](https://github.com/Cyb3rWard0g/ThreatHunter-Playbook/tree/master/signatures/sigma/win_ad_replication_user_backdoor.yml) |

## References
* https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-adts/1522b774-6464-41a3-87a5-1e5633c3fbbb
* https://docs.microsoft.com/en-us/windows/desktop/adschema/c-domain
* https://docs.microsoft.com/en-us/windows/desktop/adschema/c-domaindns
* http://www.harmj0y.net/blog/redteaming/a-guide-to-attacking-domain-trusts/
* https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2003/cc782376(v=ws.10)
* https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-drsr/f977faaa-673e-4f66-b9bf-48c640241d47