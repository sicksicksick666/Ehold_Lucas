# History of Virtualization

> Ausarbeitung – Abgabe 1, VICA SS26 (Hochschule-Burgenland, BITI)
> Lucas Ehold

## Worum handelt es sich?

**Virtualisierung** beschreibt die Technik, physische Ressourcen eines Computers – also CPU, Speicher und Netzwerk – durch eine zusätzliche Software- oder Firmwareschicht so zu *abstrahieren*, dass mehrere voneinander isolierte, logische Systeme parallel auf derselben Hardware laufen können. Jedes dieser Systeme „sieht" eine eigene, vollständige Maschine, obwohl es sich in Wirklichkeit Ressourcen mit anderen virtuellen Instanzen teilt.

Die *Geschichte der Virtualisierung* beschreibt eine fast 60 Jahre andauernde Reise: Von hochpreisigen Mainframes der 1960er-Jahre, über das fast vollständige Vergessen der Technologie in den 80ern und 90ern bis hin zur heutigen Allgegenwart in Cloud-, Server- und Container-Umgebungen. 

## Warum Virtualisierung?

Das Hauptziel der Virtualisierung ist damals wie heute dasselbe geblieben: Es ermöglicht die gleichzeitige Ausführung mehrerer unabhängiger Systeme in einer einzigen Rechnerumgebung, um die Hardware optimal auszunutzen.

Das Konzept geht auf die späten 1960er und frühen 1970er Jahre zurück, als IBM das "Time-Sharing" für Großrechner entwickelte. Dadurch konnten mehrere Nutzer teure Rechenressourcen teilen, was die Kosten drastisch senkte.

Moderne Server verfügen über so viel Kapazität, dass sie von einer einzelnen Anwendung ("Workload") kaum noch effizient ausgelastet werden können.

In heutigen Rechenzentren wird Virtualisierung genutzt, um physische Hardware von der Software zu entkoppeln (Abstraktion). Dabei werden große Pools an Ressourcen gebildet und den Nutzern in Form von flexiblen, skalierbaren "virtuellen Maschinen" zur Verfügung gestellt.

Dies führt zu einer deutlich besseren Ressourcenauslastung und vereinfacht gleichzeitig das Management von Rechenzentren.

Heute ist der Kontext anders, aber die Motivation ähnlich: Konsolidierung, Auslastungsoptimierung, Isolation, schnellere Bereitstellung und Cloud-Skalierung.

## Die wichtigsten Epochen im Überblick

| Jahrzehnt | Schlüsselereignis | Bedeutung |
|-----------|-------------------|-----------|
| 1960er | IBM CP-40 / CP-67 | Erste virtuelle Maschinen überhaupt |
| 1970er | IBM VM/370, Popek & Goldberg | Kommerzialisierung & Theorie |
| 1980er–90er | x86-PC-Boom | Virtualisierung gerät in Vergessenheit |
| Ende 1990er | VMware-Gründung (1998) | Renaissance auf Standardhardware |
| 2000er | Xen, Intel VT-x / AMD-V, KVM | Hardware-Unterstützung & Open Source |
| 2010er | Docker (2013), Kubernetes (2014) | Container & Cloud-native |
| 2020er | Firecracker, Confidential Computing | MicroVMs, sichere Mehrmandantenfähigkeit |

### Mainframe-Ära (1960er – 1970er)

Den Grundstein legte IBM am *Cambridge Scientific Center*. Mit dem **CP-40** (1964–1967) entstand das erste System, das eine echte virtuelle Maschine pro Benutzer bereitstellte. Daraus wurde das berühmte **CP-67** und schließlich – als erstes kommerzielles Produkt – **VM/370** im Jahr 1972. Konzepte wie der *Virtual Machine Monitor (VMM)*, später bekannt als **Hypervisor**, wurden hier erstmals umgesetzt.

1974 veröffentlichten **Gerald Popek** und **Robert Goldberg** ihren legendären Aufsatz *„Formal Requirements for Virtualizable Third Generation Architectures"*. Sie formulierten drei Anforderungen, die eine CPU für effiziente Virtualisierung erfüllen muss:

- **Equivalence** – Programme verhalten sich in der VM identisch wie auf echter Hardware.
- **Resource Control** – Der VMM behält jederzeit die Kontrolle über die physischen Ressourcen.
- **Efficiency** – Ein „statistisch dominanter" Anteil der Instruktionen läuft direkt auf der Hardware.

Diese Kriterien sind bis heute relevant – sie erklären, warum die x86-Architektur jahrzehntelang als „nicht virtualisierbar" galt.

### Der Niedergang in den 80ern und 90ern

Mit dem Aufstieg günstiger Mikrocomputer wie IBM-PC, Apple Macintosh und später Windows-Servern verlor Virtualisierung dramatisch an Bedeutung. Das Mantra lautete *„one application, one server"*. Hardware wurde billig, also leistete man sich für jede Anwendung einen eigenen Rechner – mit dem bekannten Effekt schlechter Auslastung.

Zusätzlich war die **x86-Architektur problematisch**: Sie verfügt über *sensitive non-privileged instructions*, die im User-Mode silently andere Werte zurückgeben als im Kernel-Mode. Damit war die Popek-Goldberg-Bedingung verletzt, klassische Trap-and-Emulate-Virtualisierung schlicht unmöglich.

 Auf echten Virtualisierungs-Architekturen (wie den alten IBM-Mainframes) erzeugte ein Gastsystem beim Ausführen privilegierter Befehle automatisch einen Fehler (Trap). Der Hypervisor fing diesen Fehler ab und führte die Aktion sicher aus.Stille Ausführung: Auf x86-Prozessoren liefen diese sensiblen Befehle (wie das Deaktivieren von Interrupts) im unprivilegierten Modus einfach weiter oder wurden ignoriert, ohne den Hypervisor zu informieren.Unsicherheit: Dadurch konnte ein Gastsystem (die virtuelle Maschine) heimlich Systeminformationen auslesen oder das gesamte Host-System gefährden

### Renaissance: VMware, Xen und Hardware-Unterstützung

1998 gründeten Diane Greene, Mendel Rosenblum und weitere Forschende der *Stanford University* die Firma **VMware**. Ihr Trick: **Binary Translation** – problematische x86-Instruktionen werden zur Laufzeit umgeschrieben. 1999 erschien VMware Workstation, 2001 dann der bahnbrechende **ESX Server**, ein *Type-1-Hypervisor*, der direkt auf der Hardware läuft.

Die Binary Translation (Binärübersetzung) ist eine Schlüsseltechnologie von VMware, die es ermöglicht, ein Betriebssystem in einer virtuellen Maschine auszuführen, ohne dass das Betriebssystem speziell dafür angepasst oder geändert werden muss.

Die Funktionsweise und der Zweck lassen sich kurz zusammenfassen:
Das Problem: Normalerweise hat das Betriebssystem (das "Gast-System") die volle Kontrolle über die Hardware. In einer virtualisierten Umgebung versucht das Gast-System, bestimmte privilegierte Befehle direkt an die physische CPU zu senden. Das führt jedoch zu Sicherheitsrisiken oder Systemabstürzen, wenn mehrere Systeme sich die Hardware teilen.

Die Lösung: Hier greift die VMware Binary Translation. Der Hypervisor (die Virtualisierungsschicht) überwacht den Code des Gast-Systems in Echtzeit (Dynamic Binary Translation). Kritische und unsichere Befehle werden im laufenden Betrieb abgefangen und in sichere, für die virtuelle Umgebung angepasste Anweisungen übersetzt, die dann von der physischen CPU ausgeführt werden.

Vorteil: Durch dieses Verfahren ist sogenannte Vollvirtualisierung möglich. Das bedeutet, Gast-Betriebssysteme laufen völlig isoliert und können eingesetzt werden, als würden sie auf echter, physischer Hardware laufen

Parallel entwickelte die *University of Cambridge* ab 2003 das Open-Source-Projekt **Xen**, das auf einen anderen Ansatz setzte: **Paravirtualisierung**. Gastsysteme werden leicht modifiziert, damit sie kooperativ mit dem Hypervisor sprechen – schneller, aber mit angepassten Gast-Kerneln.

Den endgültigen Durchbruch brachten **Intel VT-x (2005)** und **AMD-V (2006)**: Prozessorhersteller fügten neue Befehlssatz-Erweiterungen und einen zusätzlichen Privilegienring („Ring -1") hinzu, sodass ein Hypervisor sauber von Gastsystemen abgegrenzt werden kann – Popek & Goldberg waren auf x86 endlich erfüllt. Auf dieser Basis entstand 2007 **KVM** (Kernel-based Virtual Machine) als Teil des Linux-Kernels, 2008 brachte Microsoft **Hyper-V** mit Windows Server 2008.

### Container und Cloud (2010er)

Eine zweite Welle der Virtualisierung erfolgte auf Betriebssystem-Ebene. Unix kannte mit `chroot` (1979) und FreeBSD mit *Jails* (2000) schon früh Isolationsmechanismen. Solaris brachte 2004 *Zones*, der Linux-Kernel mit **cgroups** und **namespaces** (ab 2008) die nötigen Bausteine. Auf dieser Grundlage erschien 2013 **Docker** und machte Container massentauglich. **Kubernetes** (2014, ursprünglich von Google) lieferte 2015 mit Version 1.0 die Orchestrierung dazu.

Zur selben Zeit entstanden öffentliche Clouds: **Amazon EC2** startete 2006, **Microsoft Azure** 2010, **Google Cloud Platform** 2011 – allesamt im Kern Virtualisierungs-Plattformen.



## (Grobe) Technische Funktionsweise

Ein **Hypervisor** (auch *Virtual Machine Monitor, VMM*) ist die Software, die VMs erzeugt und verwaltet. Vereinfacht:

1. **Trap & Emulate**: Privilegierte Gast-Instruktionen erzeugen einen Trap, der Hypervisor emuliert das gewünschte Verhalten.
2. **Memory Virtualization**: Über *Shadow Page Tables* oder hardwareunterstützte Mechanismen (Intel EPT / AMD RVI) erhält jede VM einen eigenen Adressraum.
3. **I/O-Virtualisierung**: Geräte werden entweder emuliert (z. B. virtuelle NICs), paravirtualisiert (z. B. `virtio`) oder per *PCI-Passthrough / SR-IOV* direkt durchgereicht.

```text
┌──────────────────────────────────────────────────────────────┐
│                       Physische Hardware                     │
│  (CPU mit VT-x/AMD-V, RAM, NIC, Disk, ...)                   │
├──────────────────────────────────────────────────────────────┤
│              Type-1 Hypervisor (z. B. ESXi, KVM)             │
├───────────────┬──────────────┬──────────────┬────────────────┤
│   Gast-VM 1   │  Gast-VM 2   │  Gast-VM 3   │   Container-   │
│   Linux       │  Windows     │  Linux       │   VM (k8s)     │
│ Apache, DB    │  AD, IIS     │  K8s Worker  │   Pods/cgroups │
└───────────────┴──────────────┴──────────────┴────────────────┘
```

## Gängige Produkte, Hersteller und Projekte

| Kategorie | Vertreter |
|-----------|-----------|
| Type-1 Hypervisor | **VMware ESXi**, **Microsoft Hyper-V**, **KVM**, **Xen**, **Proxmox VE**, Nutanix AHV |
| Type-2 Hypervisor | **VirtualBox** (Oracle), **VMware Workstation/Fusion**, Parallels Desktop, **QEMU** |
| Container | **Docker**, **Podman**, **containerd**, **CRI-O**, LXC/LXD |
| Orchestrierung | **Kubernetes**, OpenShift, Nomad, Docker Swarm |
| Public Cloud (auf VM-Basis) | **AWS EC2**, **Azure Virtual Machines**, **Google Compute Engine**, Exoscale, Hetzner Cloud |
| MicroVMs / Spezial | **AWS Firecracker**, Kata Containers, gVisor |

## Anwendungsbeispiel

Ein typischer mittelständischer Betrieb betreibt zehn ehemals eigenständige Server (Mail, ERP, Dateiserver, Domaincontroller, …) heute virtualisiert auf zwei physischen Hosts. Mittels **vMotion** lassen sich VMs im laufenden Betrieb zwischen den Hosts verschieben – Wartung wird zur Routine ohne Downtime. Dasselbe Unternehmen nutzt zusätzlich eine kleine *Kubernetes*-Umgebung für moderne Web-Workloads, die wiederum in VMs auf demselben Cluster läuft – ein eindrückliches Beispiel dafür, wie sich die Virtualisierungs-Ebenen heute *stapeln*.

## Fazit

Virtualisierung ist kein neues Phänomen, sondern eine Idee aus den 1960ern, die nach einer langen Pause durch x86-Hardware-Erweiterungen und Open-Source-Innovationen ein zweites Leben fand. Sie ist die Grundlage praktisch jeder modernen Cloud und jedes Container-Stacks.

## Quellen

- Popek, G. J., & Goldberg, R. P. (1974). *Formal Requirements for Virtualizable Third Generation Architectures*. Communications of the ACM, 17(7), 412–421. <https://dl.acm.org/doi/10.1145/361011.361073>
- Goldberg, R. P. (1974). *Survey of Virtual Machine Research*. IEEE Computer, 7(6), 34–45.
- Creasy, R. J. (1981). *The Origin of the VM/370 Time-Sharing System*. IBM Journal of R&D. <https://www.cs.cornell.edu/courses/cs6411/2018sp/papers/creasy81.pdf>
- VMware: *A History of Virtualization*. <https://www.vmware.com/topics/virtualization>
- Intel Corporation (2005): *Intel Virtualization Technology Specification for the IA-32 Architecture*.
- The Linux Foundation: *KVM – Kernel-based Virtual Machine*. <https://www.linux-kvm.org/>
- Barham, P. et al. (2003): *Xen and the Art of Virtualization*. SOSP '03. <https://www.cl.cam.ac.uk/research/srg/netos/papers/2003-xensosp.pdf>
- Merkel, D. (2014): *Docker: Lightweight Linux Containers for Consistent Development and Deployment*. Linux Journal. <https://www.linuxjournal.com/content/docker-lightweight-linux-containers-consistent-development-and-deployment>
- AWS: *Firecracker MicroVM*. <https://firecracker-microvm.github.io/>
- https://docs.oracle.com/cd/E26996_01/E18549/html/BHCCIJFC.html
