-- Denetim uyarısı 0028/0029: public.rls_auto_enable() SECURITY DEFINER ve
-- anon/authenticated tarafından /rest/v1/rpc üzerinden çağrılabilir durumdaydı.
--
-- Bu fonksiyonu biz yazmadık; proje kurulurken "Enable automatic RLS"
-- seçildiği için Supabase oluşturdu. RETURNS event_trigger olduğundan
-- doğrudan RPC çağrısı zaten hata verir, ama ucu açıkta bırakmanın gereği yok.
--
-- İlk deneme anon ve authenticated'tan revoke etmekti; İŞE YARAMADI.
-- proacl '{=X/postgres,...}' gösterdi: Postgres her yeni fonksiyona
-- varsayılan olarak PUBLIC rolüne EXECUTE veriyor, anon/authenticated de
-- yetkiyi oradan miras alıyor. Doğru hamle PUBLIC'ten almak.

revoke execute on function public.rls_auto_enable() from anon, authenticated;
revoke execute on function public.rls_auto_enable() from public;

-- DDL çalıştıran rollere açıkça bırakılır.
grant execute on function public.rls_auto_enable() to postgres, service_role;

-- Doğrulandı (2026-09-18):
--   anon/authenticated has_function_privilege -> false, service_role -> true
--   Geçici tablo oluşturulup otomatik RLS'in hâlâ çalıştığı teyit edildi
--   (relrowsecurity = true), yani olay tetikleyicisi bozulmadı.
