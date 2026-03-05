import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Eye, EyeOff, Zap, Shield, BarChart3, ArrowRight } from "lucide-react";

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(
        error.response?.data?.detail ||
          "Login failed. Please check your credentials.",
      );
    } finally {
      setLoading(false);
    }
  };

  const features = [
    {
      icon: <Zap className="w-5 h-5" />,
      title: "Lightning Fast",
      desc: "Process 100K+ tasks per hour with distributed workers",
    },
    {
      icon: <Shield className="w-5 h-5" />,
      title: "Enterprise Secure",
      desc: "JWT authentication, RBAC & encrypted communications",
    },
    {
      icon: <BarChart3 className="w-5 h-5" />,
      title: "Real-time Insights",
      desc: "Live monitoring, analytics & smart alerting",
    },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Left Panel — Branding */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden bg-gradient-to-br from-slate-900 via-primary-950 to-slate-900 flex-col justify-between p-12">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 -right-32 w-80 h-80 bg-violet-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-16 left-1/3 w-72 h-72 bg-cyan-500/8 rounded-full blur-3xl" />
          {/* Grid pattern overlay */}
          <div
            className="absolute inset-0 opacity-[0.04]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
              backgroundSize: "60px 60px",
            }}
          />
        </div>

        {/* Logo */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-11 h-11 bg-gradient-to-br from-primary-400 to-violet-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/25">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">
              TaskFlow
            </span>
          </div>
          <p className="text-sm text-slate-400 ml-14">
            Distributed Task Queue System
          </p>
        </div>

        {/* Hero text */}
        <div className="relative z-10 max-w-lg">
          <h1 className="text-4xl xl:text-5xl font-extrabold text-white leading-tight tracking-tight mb-6">
            Orchestrate tasks <span className="text-gradient">at scale</span>
          </h1>
          <p className="text-lg text-slate-300 leading-relaxed mb-12">
            A production-grade distributed task queue built for reliability,
            visibility, and speed. Monitor, manage, and scale your workloads
            with confidence.
          </p>

          {/* Feature list */}
          <div className="space-y-6">
            {features.map((f, i) => (
              <div
                key={i}
                className="flex items-start gap-4 animate-fade-in"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div className="w-10 h-10 rounded-lg bg-white/[0.07] border border-white/[0.08] flex items-center justify-center text-primary-400 flex-shrink-0">
                  {f.icon}
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm mb-0.5">
                    {f.title}
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    {f.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom stats */}
        <div className="relative z-10 flex gap-8">
          {[
            { label: "Tasks/hr", value: "100K+" },
            { label: "Uptime", value: "99.9%" },
            { label: "Latency", value: "<50ms" },
          ].map((stat, i) => (
            <div key={i}>
              <div className="text-2xl font-extrabold text-white">
                {stat.value}
              </div>
              <div className="text-xs text-slate-500 uppercase tracking-wider mt-0.5">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12 bg-slate-50">
        <div className="w-full max-w-[420px]">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-10">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-violet-600 rounded-xl mb-4 shadow-lg shadow-primary-500/25">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">TaskFlow</h1>
            <p className="text-slate-500 text-sm mt-1">
              Distributed Task Queue
            </p>
          </div>

          {/* Heading */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
              Welcome back
            </h2>
            <p className="text-slate-500 mt-1.5">
              Sign in to continue to your dashboard
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3.5 rounded-xl text-sm">
              <div className="w-5 h-5 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-red-600 text-xs font-bold">!</span>
              </div>
              <span className="font-medium">{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="username"
                className="block text-sm font-semibold text-slate-700 mb-2"
              >
                Username
              </label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400
                           focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 outline-none transition-all"
                placeholder="Enter your username"
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-semibold text-slate-700 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 pr-12 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400
                             focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 outline-none transition-all"
                  placeholder="Enter your password"
                  required
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800
                         text-white py-3.5 rounded-xl font-semibold text-[15px] transition-all duration-200
                         disabled:opacity-60 disabled:cursor-not-allowed
                         shadow-lg shadow-primary-600/25 hover:shadow-xl hover:shadow-primary-600/30
                         flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <>
                  <div
                    className="loading-spinner"
                    style={{ width: 20, height: 20, margin: 0 }}
                  >
                    <div className="spinner-ring" />
                    <div className="spinner-ring" />
                  </div>
                  Signing in…
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Demo credentials */}
          <div className="mt-8 bg-white border border-slate-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1.5 h-1.5 rounded-full bg-primary-500" />
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                Demo Credentials
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="text-xs text-slate-400 block mb-1">
                  Username
                </span>
                <code className="text-sm font-mono font-semibold text-slate-800 bg-slate-50 px-2.5 py-1 rounded-lg block text-center">
                  admin
                </code>
              </div>
              <div>
                <span className="text-xs text-slate-400 block mb-1">
                  Password
                </span>
                <code className="text-sm font-mono font-semibold text-slate-800 bg-slate-50 px-2.5 py-1 rounded-lg block text-center">
                  admin123
                </code>
              </div>
            </div>
          </div>

          {/* Register link */}
          <p className="text-center text-sm text-slate-500 mt-6">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="text-primary-600 font-semibold hover:text-primary-700 transition-colors"
            >
              Create one
            </Link>
          </p>

          {/* Footer */}
          <p className="text-center text-slate-400 text-xs mt-8">
            &copy; {new Date().getFullYear()} TaskFlow &middot; Built with
            React, TypeScript &amp; FastAPI
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
