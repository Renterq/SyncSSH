# SyncSSH 🚀

SyncSSH, birden fazla Linux sunucusunu tek bir modern arayüz üzerinden eşzamanlı olarak yönetmenizi, izlemenizi ve kontrol etmenizi sağlayan güçlü ve **güvenli** bir masaüstü SSH yöneticisidir. 

Ağ yöneticileri, siber güvenlik uzmanları ve sistem mühendisleri için geliştirilmiş olan bu araç; sunucularınızın anlık kaynak tüketimlerini takip ederken, aynı anda onlarca makineye toplu komut gönderme imkanı sunar.

## ✨ Öne Çıkan Özellikler

* **🔒 Yüksek Güvenlikli Kasa (Vault):** Sunucu kimlik bilgileriniz düz metin olarak saklanmaz. Tüm verileriniz, belirlediğiniz bir ana şifre kullanılarak **AES (Fernet)** mimarisiyle şifrelenir. 
* **🔑 Sistem Entegrasyonu:** İşletim sisteminizin yerel anahtar zincirini (`keyring`) kullanarak ana şifrenizi güvenle hatırlar, her girişte şifre yazma derdini ortadan kaldırır.
* **📊 Canlı Dashboard:** Sunucularınızın CPU, RAM ve Disk kullanımlarını gerçek zamanlı olarak şık dairesel grafiklerle izleyin.
* **⚡ Toplu Komut Çalıştırma (Bulk SSH):** Tek bir komutu (örn: `apt-get update`) sisteme kayıtlı tüm sunuculara aynı anda gönderin ve çıktıları ızgara (grid) görünümünde eşzamanlı takip edin.
* **💻 Tekli Kontrol (Single SSH):** Seçtiğiniz spesifik bir sunucuya hızlıca bağlanın ve özel terminal temalarıyla komutlarınızı çalıştırın.
* **📁 Gelişmiş Sunucu Yönetimi:** Sunucularınızı renklendirin, sıralayın ve son kullanma/kiralama tarihlerini belirleyerek düzenli tutun. Eski (şifresiz) `servers.json` dosyalarınızı otomatik olarak şifreli yeni formata dönüştürür.
* **🔔 Akıllı Bildirimler:** Kiralama süresi dolmak üzere olan veya süresi geçen sunucularınız için otomatik uyarılar alın.

## 🚀 Yakında Gelecekler (Coming Soon)

Projeyi kurmak için Python bağımlılıklarıyla uğraşmak istemeyen kullanıcılar için tek tıklamayla çalıştırılabilir paketler çok yakında hazır olacak:
* **Windows:** `.exe` sürümü
* **Linux:** `.appimage` sürümü

## 🛠️ Kurulum (Geliştiriciler İçin)

Kaynak kodundan çalıştırmak isterseniz aşağıdaki adımları izleyebilirsiniz:

1. Depoyu klonlayın:
   ```bash
   git clone [https://github.com/Renterq/SyncSSH.git](https://github.com/Renterq/SyncSSH.git)
   cd SyncSSH
