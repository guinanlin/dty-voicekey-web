/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ["pdfkit"],
  // DevContainer 经宿主机端口映射访问时，允许 HMR / dev 资源跨域
  allowedDevOrigins: ["localhost", "127.0.0.1"],
};

export default nextConfig;
