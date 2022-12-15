# TinkerBot
Below you can find documentation for setting up everything you need. This assumes you're using Windows 10, but it should be more than doable to adapt this to other operating systems.

## Environment Creation
Make a droplet on DigitalOcean running Ubuntu 22.10 x64, and create an SSH key for it (I used `ssh-keygen` via OpenSSH). Keep track of its public IP, you'll need it a lot.
Put the public key into DigitalOcean, and save your private key wherever you like. After the droplet is created, connect to it through SSH using `ssh -i "PATH:TO\PRIVATE\KEY\FILE" root@public_droplet_ip`. Then, perform a system update using `apt update && apt upgrade`. 

## Optional - Changing SSH Port
**Important:** If you don't follow this step, remember to make an inbound firewall rule that opens port 22 using type `SSH`.

Run `nano /etc/ssh/sshd_config`, and then find the line that says `#Port 22`. Uncomment out this line and change the port to something else of your choosing.
Go into your DigitalOcean droplet panel, and under the `Networking` tab, scroll down to the bottom and create a new firewall. Leave the default settings, but under `Inbound Rules`, 
add a new rule of type `Custom` to allow TCP traffic from the port you chose (between 10000 and 65536). Apply this firewall to your droplet.

## Database Creation
Now, we'll install MariaDB. Run `apt install mariadb-server` and then `mysql_secure_installation`. I chose the following options:

* `Root Password`: None
* `unix_socket authentication`: No
* `Change root password`: No
* `Remove Anonymous Users`: Yes
* `Disallow Remote Root Login`: Yes
* `Remove Test Database`: Yes
* `Reload Privilege Tables`: Yes

## Setting up Database Users
Now, we'll initialize users on the database. Access the SQL terminal by running `mariadb`. Create a new database named `work` using `CREATE DATABASE work;`. Then, create a new user named `bot_access` on the `localhost` hostname by running `CREATE USER 'bot_access'@localhost;`, so that only a program running on the DigitalOcean droplet could access it. We don't need a password due to the prior mentioned restriction.

Optionally, you can setup remote access from your PC by doing the following:
* Get your public IP from a website like https://whatismypublicip.com
* Created a new `admin` user that could only login from this IP: `CREATE USER 'admin'@'IP' IDENTIFIED BY 'password';`
* Grant admin permissions to our new user: `GRANT ALL ON *.* TO 'admin'@'IP';`

## Optional - Allowing Remote Connections to the Database
This is only needed if you ever plan on testing your DB from your own machine (or you plan on running the bot from a machine that isn't the droplet)
Enter the MariaDB config using `nano /etc/mysql/my.cnf`, then add these lines to it (for me, the file only had a few client-server definitions and some `!includedir` statements. Your mileage may vary):
```conf
[mysqld]
skip-networking=0
skip-bind-address
```
Restart the service: `systemctl restart mysqld`. 
Finally, adjust the firewall by creating a new inbound firewall rule of type `MySQL` (should have port 3306) with the source of your public IP.

To test, install the `mariadb` library from pip and execute the following code:
```python
import mariadb

db_conn = mariadb.connect(
    user="admin",
    password="password",
    host="droplet_ip",
    port=3306,
    database="work"
)

db_cursor = db_conn.cursor()
db_cursor.execute("CREATE TABLE TEMP (a int);")
db_cursor.execute("INSERT INTO TEMP VALUES (55);")
db_cursor.execute("INSERT INTO TEMP VALUES (14);")

db_conn.close()
```
In your SSH session, access the MariaDB terminal, indicate you are using the `work` database, and execute the following query:
```sql
MariaDB [work]> SELECT * FROM TEMP;
+------+
| a    |
+------+
|   55 |
|   14 |
+------+
```
You can now drop this table.

## Initializing Database Structure
Run `database_obj.create_db(DatabaseConnection.engine, DatabaseConnection.session)` to create the database tables and initialize some fields in the `Status` and `Department` tables. 

## Setting up FileBrowser with Web Access

### Installing FileBrowser
Install FileBrowser by executing the following commands (from [here](https://filebrowser.org/installation/)):
```bash
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash
filebrowser -r /path/to/your/files
```
Use `tmux` to run `filebrowser`, and then exit the tmux session using `CTRL + B, D` and run `curl localhost:8080` to make sure FileBrowser is running properly.

### Setting up a Domain
Note that for the purposes of demonstration, I will be using `example.com` as my domain.

I used NameCheap, but anything should work. On your domain dashboard, go to DNS configuration, and remove all existing host records.
Create a new A Record with the `host` value of `files` (so that your FileBrowser setup can be accessed from the subdomain of `files`. If you don't want this, use `*`.), and set the value to be your droplet's public IP.

### Setting up Apache
This section is based off [this](https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-20-04) guide.

#### Installing
Run `sudo apt update && sudo apt install apache2`.
Add 2 new outbound firewall rules of type `HTTP` and `HTTPS` for `All IPv4` and `All IPv6` traffic on ports 80 and 443 respectively.
Make sure apache is running by using `systemctl status apache2`, then try connecting to it using your droplet's public IP in a web browser.

#### Site Configuration
Create a configuration file for your domain using `nano /etc/apache2/sites-available/files.example.com.conf`, and paste the following contents into it, editing values where necessary:
```conf
<VirtualHost *:80>
        ServerAdmin my_email@gmail.com
        ServerName files.example.com

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        ProxyPreserveHost On

        ProxyPass / http://127.0.0.1:8080/
        ProxyPassReverse / http://127.0.0.1:8080/

        RewriteEngine on
        RewriteCond %{SERVER_NAME} = files.example.com
        RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [L,NE,R=permanent]

        RewriteCond %{HTTP_HOST} ^198\.192\.0\.100$
        RewriteRule ^(.*)$ https://files.example.com/$1 [L,R=301]

</VirtualHost>
```
This will setup HTTP => HTTPS redirection, a reverse proxy to FileBrowser on port `8080` (this may need changing if you configure FileBrowser), and IP => URL redirection.
Note that you need to edit this line (`RewriteCond %{HTTP_HOST} ^198\.192\.0\.100$`) to be your public IP. Just paste it in-between the caret and dollar sign characters, and escape the dots.

Enable this site and disable the default one using `a2ensite files.example.com.conf && a2dissite 000-default.conf`, and check for configuration errors: `apache2ctl configtest`. You should receive no errors. Restart the Apache service: `systemctl restart apache2`. 

### Setting up HTTPS via Let's Encrypt
This is based off [this](https://www.digitalocean.com/community/tutorials/how-to-secure-apache-with-let-s-encrypt-on-ubuntu-20-04) guide.

If you followed the above successfully, connecting to your domain should fail, as HTTPS isn't enabled, but any HTTP connection redirects to HTTPS.
To fix this, we need to secure our domain. 

Install CertBot using `apt install certbot python3-certbot-apache`, and run it using `certbot --apache`. Enter the email address specified in the configuration file, accept any T&C, and select the `files.example.com` domain. Select `1: No redirect` to not configure the site for HTTPS redirection, as we have already done this in the previous step. 

Now, connect to `files.example.com` via a web browser, and you should be greeted with a login page. 
