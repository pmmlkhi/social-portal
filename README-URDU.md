# سوشل میڈیا پورٹل — سیٹ اپ گائیڈ (اردو)

آپ کا اپنا سوشل میڈیا مینجمنٹ پورٹل: ایک جگہ سے پوسٹنگ، ایک جگہ سارے انباکس، اور بوٹ کے جوابات کی ترتیب۔

## مرحلہ 1 — کوڈ کو آن لائن چلائیں

1. یہ `social-portal` فولڈر GitHub پر اپ لوڈ کریں۔
2. [render.com](https://render.com) پر مفت اکاؤنٹ بنائیں۔
3. **New → Web Service** → اپنا GitHub repo منتخب کریں (render.yaml خود سب سیٹ کر دے گا)۔
4. Environment variables میں یہ بھریں:
   - `PORTAL_PASSWORD` — پورٹل کے لاگ اِن کے لیے اپنا پاس ورڈ (ضروری)
   - `VERIFY_TOKEN` — خود کوئی مشکل لفظ بنائیں (Meta webhook کے لیے)
   - `PAGE_ACCESS_TOKEN` — مرحلہ 2 سے ملے گا
   - `WHATSAPP_TOKEN` اور `WHATSAPP_PHONE_NUMBER_ID` — مرحلہ 3 سے ملیں گے (اختیاری)
5. Deploy کریں۔ آپ کو ایڈریس ملے گا جیسے `https://aap-ka-portal.onrender.com`

## مرحلہ 2 — فیس بک پیج جوڑیں

1. [developers.facebook.com](https://developers.facebook.com) پر App بنائیں (قسم: Business)۔
2. App میں **Messenger** پروڈکٹ شامل کریں۔
3. اپنا فیس بک پیج Connect کریں اور **Page Access Token** بنائیں۔
4. یہ ٹوکن Render میں `PAGE_ACCESS_TOKEN` میں ڈالیں۔
5. Webhook میں:
   - Callback URL: `https://aap-ka-portal.onrender.com/webhook`
   - Verify Token: وہی جو `VERIFY_TOKEN` میں لکھا تھا
   - `messages` فیلڈ سبسکرائب کریں۔

## مرحلہ 3 — واٹس ایپ جوڑیں (اختیاری)

1. اسی App میں **WhatsApp** پروڈکٹ شامل کریں۔
2. اپنا WhatsApp Business نمبر (03702855501) شامل کریں۔
3. Token اور Phone Number ID نوٹ کر کے Render میں ڈالیں۔
4. Webhook میں وہی Callback URL دے کر `messages` سبسکرائب کریں۔

## مرحلہ 4 — استعمال

- براؤزر میں پورٹل کھولیں، `PORTAL_PASSWORD` سے لاگ اِن کریں۔
- **پوسٹ لکھیں:** متن لکھیں → ابھی شائع کریں یا شیڈول کریں۔
- **بوٹ جوابات:** 17 تیار جوابات دیکھیں/بدلیں — تبدیلی فوراً نافذ۔
- **انباکس:** فیس بک اور واٹس ایپ کے پیغامات اور بوٹ کے جوابات ایک جگہ۔

## نوٹ

- پہلی بار deploy پر `data/` فولڈر خالی ہوگا — `faqs.json` اسی پیکج میں شامل ہے۔
- پورٹل کا پاس ورڈ کسی کو نہ بتائیں۔
- اگلے مراحل (انسٹاگرام وغیرہ) بعد میں شامل کیے جائیں گے۔
