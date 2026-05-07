# SyncSSH 🚀

SyncSSH, birden fazla Linux sunucusunu tek bir modern arayüz üzerinden eşzamanlı olarak yönetmenizi, izlemenizi ve kontrol etmenizi sağlayan güçlü bir masaüstü SSH yöneticisidir. 

Ağ yöneticileri, siber güvenlik uzmanları ve sistem mühendisleri için geliştirilmiş olan bu araç; sunucularınızın anlık kaynak tüketimlerini takip ederken, aynı anda onlarca makineye toplu komut gönderme imkanı sunar.

🔗 **Proje Bağlantısı:**

## ✨ Öne Çıkan Özellikler

*   **📊 Canlı Dashboard:** Sunucularınızın CPU, RAM ve Disk kullanımlarını gerçek zamanlı olarak şık dairesel grafiklerle izleyin.
*   **⚡ Toplu Komut Çalıştırma (Bulk SSH):** Tek bir komutu (örn: `apt-get update`) sisteme kayıtlı tüm sunuculara aynı anda gönderin ve çıktıları ızgara (grid) görünümünde eşzamanlı takip edin.
*   **💻 Tekli Kontrol (Single SSH):** Seçtiğiniz spesifik bir sunucuya hızlıca bağlanın ve özel terminal temalarıyla komutlarınızı çalıştırın.
*   **📁 Gelişmiş Sunucu Yönetimi:** Sunucularınızı IP, Port, Kullanıcı Adı ve Şifre bilgileriyle kaydedin. Onları renklendirin, sıralayın ve son kullanma/kiralama tarihlerini belirleyin.
*   **🔔 Akıllı Bildirimler:** Kiralama süresi dolmak üzere olan veya süresi geçen sunucularınız için otomatik uyarılar alın.
*   **🎨 Özelleştirilebilir Arayüz:** Açık/Koyu mod desteği ve sunuculara özel terminal temaları (Hacker, Okyanus vb.).
*   **🔒 Yerel Veri Saklama:** Verileriniz buluta gitmez, cihazınızda şifrelenmemiş/yerel JSON dosyaları olarak tutulur.

## 🚀 Yakında Gelecekler (Coming Soon)

Projeyi kurmak için Python bağımlılıklarıyla uğraşmak istemeyen kullanıcılar için tek tıklamayla çalıştırılabilir paketler çok yakında hazır olacak:
*   **Windows:** `.exe` sürümü
*   **Linux:** `.appimage` sürümü

## 🛡️ Güvenlik
SyncSSH, sunucu kimlik bilgilerinizi şu an için `servers.json` dosyası içerisinde düz metin (plain text) olarak saklamaktadır. Kendi kişisel veya güvenli ağ ortamınızda kullanmanız tavsiye edilir. İlerleyen güncellemelerde AES tabanlı şifreleme özellikleri eklenecektir.

## 🛠️ Kurulum (Geliştiriciler İçin)

Kaynak kodundan çalıştırmak isterseniz aşağıdaki adımları izleyebilirsiniz:

1. Depoyu klonlayın:
   ```bash
   git clone [https://github.com/Renterq/SyncSSH.git](https://github.com/Renterq/SyncSSH.git)
   cd SyncSSH

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install customtkinter paramiko tkcalendar
