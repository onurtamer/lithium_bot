import Link from 'next/link';
import {
  Shield,
  Zap,
  Users,
  BarChart3,
  ArrowRight,
  Check,
  Star,
  ChevronRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: Shield,
    title: 'Gelişmiş Güvenlik',
    description: 'AutoMod, Anti-Raid, Jail sistemi ve daha fazlası ile sunucunuzu koruyun.',
  },
  {
    icon: Users,
    title: 'Topluluk Araçları',
    description: 'Seviye sistemi, çekilişler, doğum günleri ve tepki rolleri.',
  },
  {
    icon: BarChart3,
    title: 'Detaylı Analytics',
    description: 'Sunucu aktivitesini takip edin, trendleri keşfedin.',
  },
  {
    icon: Zap,
    title: 'Anında Senkronizasyon',
    description: 'Panel değişiklikleri anında bota yansır.',
  },
];

const benefits = [
  'Sınırsız modül aktivasyonu',
  'Gerçek zamanlı dashboard',
  'Konfigürasyon versiyonlama',
  'Detaylı denetim kayıtları',
  'Öncelikli destek',
  '99.9% uptime garantisi',
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-background/80 backdrop-blur-lg">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg gradient-blurple flex items-center justify-center">
              <span className="text-white font-bold text-sm">Li</span>
            </div>
            <span className="font-bold text-xl">Lithium</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="/features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Özellikler
            </Link>
            <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Fiyatlandırma
            </Link>
            <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Dokümantasyon
            </Link>
            <Link href="/status" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Durum
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/login">Giriş Yap</Link>
            </Button>
            <Button asChild className="gap-2 gradient-blurple border-0">
              <Link href="/login">
                Dashboard'a Git
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        </div>

        <div className="container mx-auto px-4 text-center">
          <Badge variant="outline" className="mb-6 px-4 py-1.5 text-sm border-primary/50">
            <Star className="h-3 w-3 mr-2 fill-primary text-primary" />
            Premium Discord Bot Management
          </Badge>

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            Discord Sunucunuzu
            <br />
            <span className="gradient-text">Profesyonelce Yönetin</span>
          </h1>

          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            MEE6 ve Dyno kalitesinde, Türkçe destekli, kolay kullanımlı kontrol paneli.
            Moderasyon, seviye sistemi, çekilişler ve daha fazlası.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild className="gap-2 gradient-blurple border-0 text-lg px-8 py-6 glow-primary">
              <Link href="/login">
                Ücretsiz Başla
                <ArrowRight className="h-5 w-5" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="text-lg px-8 py-6">
              <Link href="/features">
                Özellikleri Keşfet
              </Link>
            </Button>
          </div>

          <p className="text-sm text-muted-foreground mt-6">
            ✓ Kredi kartı gerekmez &nbsp;•&nbsp; ✓ 5 dakikada kurulum &nbsp;•&nbsp; ✓ Türkçe destek
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 border-t border-border">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Her İhtiyacınız İçin Güçlü Modüller
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              15+ modül, 40+ komut ve sınırsız özelleştirme seçeneği ile sunucunuzu kontrol altına alın.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} className="card-hover border-border/50 bg-card/50">
                <CardContent className="pt-6">
                  <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge variant="outline" className="mb-4">Neden Lithium?</Badge>
              <h2 className="text-3xl md:text-4xl font-bold mb-6">
                Rakiplerden Bir Adım Önde
              </h2>
              <p className="text-muted-foreground mb-8">
                Lithium, modern web teknolojileri ve Discord API'nin en son özellikleri ile geliştirilmiştir.
                Kullanıcı deneyimini ön planda tutarak tasarlandı.
              </p>

              <ul className="space-y-4">
                {benefits.map((benefit) => (
                  <li key={benefit} className="flex items-center gap-3">
                    <div className="h-6 w-6 rounded-full bg-success/20 flex items-center justify-center">
                      <Check className="h-4 w-4 text-success" />
                    </div>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative">
              <div className="aspect-video rounded-xl bg-card border border-border overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-border flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-destructive/50" />
                  <div className="h-3 w-3 rounded-full bg-warning/50" />
                  <div className="h-3 w-3 rounded-full bg-success/50" />
                </div>
                <div className="p-6">
                  <div className="h-4 bg-muted rounded w-1/3 mb-4" />
                  <div className="grid grid-cols-3 gap-4">
                    <div className="aspect-square bg-muted rounded-lg" />
                    <div className="aspect-square bg-muted rounded-lg" />
                    <div className="aspect-square bg-muted rounded-lg" />
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-4 -right-4 -z-10 w-full h-full rounded-xl bg-gradient-to-br from-primary/30 to-purple-500/30 blur-xl" />
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-primary/10 to-purple-500/10">
            <CardContent className="py-12 text-center">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Hemen Başlayın
              </h2>
              <p className="text-muted-foreground max-w-xl mx-auto mb-8">
                Discord hesabınızla giriş yapın ve saniyeler içinde sunucunuzu yönetmeye başlayın.
              </p>
              <Button size="lg" asChild className="gap-2 gradient-blurple border-0">
                <Link href="/login">
                  Discord ile Giriş Yap
                  <ChevronRight className="h-5 w-5" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg gradient-blurple flex items-center justify-center">
                <span className="text-white font-bold text-sm">Li</span>
              </div>
              <span className="font-bold">Lithium</span>
            </div>

            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <Link href="/features" className="hover:text-foreground transition-colors">Özellikler</Link>
              <Link href="/docs" className="hover:text-foreground transition-colors">Dokümantasyon</Link>
              <Link href="/status" className="hover:text-foreground transition-colors">Durum</Link>
              <Link href="/privacy" className="hover:text-foreground transition-colors">Gizlilik</Link>
              <Link href="/terms" className="hover:text-foreground transition-colors">Kullanım Koşulları</Link>
            </div>

            <p className="text-sm text-muted-foreground">
              © 2026 Lithium. Tüm hakları saklıdır.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
