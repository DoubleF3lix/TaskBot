## Environment Creation
First, I made a droplet on DigitalOcean running Ubuntu 22.10 x64, and created an SSH key for it. After putting the public key into DigitalOcean, I saved my private key in `"D:\Downloads\Work DB\digitalocean_key"`. After the droplet was created, I connected to it through SSH using `ssh -i "D:\Downloads\Work DB\digitalocean_key" root@public_droplet_ip`.
Then I ran `apt update && apt upgrade`. 

## Firewall Configuration Part 1
Now, for security, changing the SSH port. Run `nano /etc/ssh/sshd_config`, and then next to `#Port 22`, uncomment out this line and change the port to something else.
Go into your DigitalOcean droplet panel, and under the `Networking` tab, scroll down to the bottom and create a new firewall. Leave the default settings, but under `Inbound Rules`, 
add a new rule of type `Custom` to allow TCP traffic from any port you choose (between 10000 and 65536). Apply this firewall to your droplet.

## Finishing Environment Creation
After a reboot, I had to install was MariaDB, which I did using `apt install mariadb-server`. I ran `mysql_secure_installation` to setup the DB, and I chose the following options:

* `Root Password`: None
* `unix_socket authentication`: No
* `Change root password`: No
* `Remove Anonymous Users`: Yes
* `Disallow Remote Root Login`: Yes
* `Remove Test Database`: Yes
* `Reload Privilege Tables`: Yes

## Setting up Database Users
After setting up the database, I accessed the SQL terminal via `mariadb`. From here, I created a new database named `work` using `CREATE DATABASE`. Then I created a new user named `bot_access` on the `localhost` hostname, so that only a program from the DigitalOcean droplet could access it. 
Now, I wanted to setup remote access from my PC, following these steps:
* First, I got my public IP from https://whatismypublicip.com.
* Then, I created a new `admin` user that could only login from my IP: `CREATE USER 'admin'@'IP' IDENTIFIED BY 'password';`.
* Granting admin permissions to our new `admin` user: `GRANT ALL ON *.* TO 'admin'@'IP';`. 

## Allowing Remote Connections In Our Database
Now, we need to make the MariaDB database accept remote connections. 
I entered the MariaDB config using `nano /etc/mysql/my.cnf`, then added these lines to it (the file only had a few client-server definitions and some `!includedir` statements. Your mileage may vary):
```conf
[mysqld]
skip-networking=0
skip-bind-address
```
Finally, we have to restart the service for these changes to take effect using `systemctl restart mysqld`. 

## Firewall Configuration Part 2
We're done configuring MariaDB, but we have one more step. In the firewall you made earlier to edit the SSH port, add a rule with a type of `MySQL` and a port range of `3306`, and remove the `All IPv4` and `All IPv6` sources, and instead paste in your public that you grabbed earlier.

## Testing The Database
Now, you should be able to connect to the database using the `mariadb` library. Make sure you install it with `pip` first. Here's the sample code I used:
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
To validate my results, I selected the database with `USE work;`, and then ran `SELECT * FROM TEMP;` in the SSH terminal, and success!
```sql
MariaDB [work]> SELECT * FROM TEMP;
+------+
| a    |
+------+
|   55 |
|   14 |
+------+
```

## Initializing Database Structure
Run `database_obj.create_db(DatabaseConnection.engine, DatabaseConnection.session)` to create the database.

## Setting up FileBrowser, Apache, and a Domain
Oh boy, this has a lot in it.
TODO