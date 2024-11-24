# **SSLE_TP1**

## **Descrição do Projeto**
O projeto **SSLE_TP1** consiste na implementação de um sistema de larga escala com foco na segurança e mitigação de ameaças cibernéticas. O sistema é composto por vários serviços, incluindo:

- **Wazuh**: Utilizado como SIEM para monitorização e deteção de ameaças.
- **Service_a**: Um serviço simples com endpoints, incluindo `/get_value` e `/block_ip`.
- **Prometheus**: Responsável por recolher métricas do `service_a` e gerar logs de eventos.
- **Consul**: Atua como registo de serviços, facilitando a descoberta e interação entre componentes.
- **Apache**: Base de dados para armazenamento de informações essenciais.
- **Postfix e SpamAssassin**: Gerem o envio de e-mails e a filtragem de spam, respetivamente.

O projeto inclui a implementação de medidas de mitigação contra ataques como DoS (Denial of Service), aproveitando a integração entre Prometheus, Wazuh e scripts personalizados, emails de spam e Shellshock.

---

## **Configuração dos Serviços**

### **1. Configuração do Spam nos E-mails**
O serviço de spam em e-mails é implementado com o container **mail-container**. Para configurar este serviço, foram necessários ajustes em 4 ficheiros:

Adicionar um utilizador:
```adduser spamd --disabled-login```

- **/etc/spamassassin/local.cf**
Descomentar as seguintes linhas:
```
rewrite_header Subject *****SPAM*****
required_score 5.0
use_bayes 1
bayes_auto_learn 1
```
Acrescentar:
```
# Custom rule to flag emails with "winner" int the body
body    BODY_CONTAINS_WINNER  /\b(winner)\b/i
score   BODY_CONTAINS_WINNER  8.0
describe BODY_CONTAINS_WINNER Email body contains the word "winner"

# Custom rule to flag emails with "winner" in the headers
header  HEADER_CONTAINS_WINNER  /(?:^|\W)(winner)(?:\W|$)/i
score   HEADER_CONTAINS_WINNER  8.5
describe HEADER_CONTAINS_WINNER Email header contains the word "winner"
```
- **/etc/default/spamassassin**:
Acrescentar:
```
SAHOME="/var/log/spamassassin/"
```
Alterar as seguintes linhas:
```
OPTIONS="--create-prefs --max-children 5 --username spamd --helper-home-dir /home/spamd/ -s /home/spamd>

CRON=1
```
- **/etc/postfix/main.cf**:
Acrescentar:
```content_filter = spamassassin```
- **/etc/postfix/master.cf**:
Alterar a linha:
```smtp      inet  n       -       y       -       -       smtpd -o content_filter=spamassassin```

Acrescentar:
```spamassassin unix -     n       n       -       -       pipe    user=spamd argv=/usr/bin/spamc -f -e    /usr/sbin/sendmail -oi -f ${sender} ${recipient}```

### **2. Configuração do Shellshock**
Para implementar a mitigação contra o ataque Shellshock, são necessários dois containers: **wazuh-container** e **apache-container**.

#### **Apache Container**
Instalar um agente do Wazuh e acrescentar no /var/ossec/etc/ossec.conf:
```
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/apache2/access.log</location>
</localfile>
```

#### **Wazuh Container**
No **wazuh-container**, fazer download de uma blacklist foram necessários ajustes em 2 ficheiros:

- **/var/ossec/etc/rules/local_rules.xml**:
Acrescentar:
```
<group name="attack,">
  <rule id="100100" level="10">
    <if_group>web|attack|attacks</if_group>
    <list field="srcip" lookup="address_match_key">etc/lists/blacklist-alienvault</list>
    <description>IP address found in AlienVault reputation database.</description>
  </rule>
</group>
```

- **/var/ossec/etc/ossec.conf**:
Na parte da ruleset acrescentar uma linha:
```<list>etc/lists/blacklist-alienvault</list>```

Acrescentar:
```
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100100</rules_id>
  <timeout>60</timeout>
</active-response>
```

### **3. Configuração de Mitigação contra DoS (Denial of Service)**
Para a mitigação contra ataques DoS, são necessários 4 containers: **wazuh-container**, **prometheus-container**, **consul-container**, e **service_a-container**.

#### **Wazuh Container**
No **wazuh-container**, foram necessárias modificações em 4 ficheiros:

- **/var/ossec/etc/decoders/local_decoder.xml**:
Acrescentar:
```
<decoder name="dos_custom">
  <prematch>^DoS attack</prematch>
</decoder>

<decoder name="dos_custom_child">
  <parent>dos_custom</parent>
  <regex offset="after_parent">^\sfrom:\s(\S+) with \d+ requests</regex>
  <order>srcip</order>
</decoder>
```
- **/var/ossec/etc/rules/local_rules.xml**:
Acrescentar:
```
<group name="dos_custom">
 <rule id="100021" level="12">
    <decoded_as>dos_custom</decoded_as>
    <description>DoS attack comming from $(srcip)!</description>
 </rule>
</group>
```
- **/var/ossec/etc/ossec.conf**:
Acrescentar:
```
<command>
  <name>block_ip</name>
  <executable>block_ip.sh</executable>
  <timeout_allowed>yes</timeout_allowed>
</command>

<active-response>
  <disabled>no</disabled>
  <command>block_ip</command>
  <location>local</location>
  <rules_id>100021</rules_id>
  <timeout>60</timeout>
</active-response>
```
- Criar o ficheiro **/var/ossec/active-response/bin/block_ip.sh**.

#### **Prometheus Container**
No **prometheus-container** é preciso instalar o agente do Wazuh como no apache-container e criar o ficheiro **log_metrics.py**.

Alterar o **/var/ossec/etc/ossec.conf** como no apache-container acrescentar:
```
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/service_check.log</location>
</localfile>
```

#### **Consul Container**
Não há modificações necessárias no **consul-container**.
Para correr o consul ```consul agent -dev -client=0.0.0.0 -data-dir=/var/consul &```

#### **Service_A Container**
No **service_a-container** basta criar o ficheiro **service.py**.