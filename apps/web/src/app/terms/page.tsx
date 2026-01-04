"use client";

import Link from "next/link";

export default function TermsOfServicePage() {
    return (
        <div className="min-h-screen bg-background">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid-lithium opacity-30 pointer-events-none" />
            <div className="fixed inset-0 gradient-radial-lithium pointer-events-none" />

            <div className="relative z-10 container mx-auto px-6 py-16 max-w-4xl">
                {/* Header */}
                <div className="mb-12">
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-8"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                        Ana Sayfaya Dön
                    </Link>

                    <h1 className="text-4xl font-bold gradient-text-lithium mb-4">
                        Hizmet Şartları
                    </h1>
                    <p className="text-muted-foreground">
                        Son güncelleme: 4 Ocak 2026
                    </p>
                </div>

                {/* Content */}
                <div className="glass-card rounded-2xl p-8 space-y-8">
                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">1. Kabul Edilen Şartlar</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Lithium Bot hizmetlerini kullanarak, bu hizmet şartlarını kabul etmiş olursunuz.
                            Eğer bu şartları kabul etmiyorsanız, lütfen hizmetlerimizi kullanmayınız.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">2. Hizmet Tanımı</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Lithium Bot, Discord sunucuları için geliştirilmiş bir yönetim ve moderasyon
                            botudur. Hizmetlerimiz, sunucu yönetimi, moderasyon araçları, otomasyon ve
                            analitik özellikleri içermektedir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">3. Kullanım Koşulları</h2>
                        <ul className="text-muted-foreground space-y-2 list-disc list-inside">
                            <li>Hizmetlerimizi yalnızca yasal amaçlar için kullanmalısınız</li>
                            <li>Discord&apos;un Hizmet Şartları ve Topluluk Kuralları&apos;na uymalısınız</li>
                            <li>Botun kötüye kullanımı veya suistimali yasaktır</li>
                            <li>Spam, taciz veya zararlı içerik oluşturmak için kullanılamaz</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">4. Hesap Güvenliği</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Hesabınızın güvenliğinden siz sorumlusunuz. Discord hesabınızın bilgilerini
                            kimseyle paylaşmayın. Hesabınızda gerçekleşen tüm etkinliklerden siz sorumlu
                            tutulursunuz.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">5. Hizmet Kesintileri</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Bakım, güncelleme veya teknik sorunlar nedeniyle hizmetlerimizde kesinti
                            yaşanabilir. Bu tür kesintiler için önceden bildirim yapmaya çalışacağız,
                            ancak acil durumlar için bu mümkün olmayabilir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">6. Değişiklikler</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Bu hizmet şartlarını herhangi bir zamanda değiştirme hakkımız saklıdır.
                            Önemli değişiklikler için kullanıcıları bilgilendireceğiz.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-2xl font-semibold text-foreground mb-4">7. İletişim</h2>
                        <p className="text-muted-foreground leading-relaxed">
                            Bu şartlarla ilgili sorularınız için bizimle iletişime geçebilirsiniz.
                        </p>
                    </section>
                </div>

                {/* Footer */}
                <div className="mt-12 text-center">
                    <p className="text-muted-foreground text-sm">
                        © 2026 Lithium Bot. Tüm hakları saklıdır.
                    </p>
                </div>
            </div>
        </div>
    );
}
