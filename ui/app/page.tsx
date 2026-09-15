"use client";
import { useRouter } from "next/navigation";
import { TokenForm } from "@/components/token-form";

export default function LoginPage() {
  const router = useRouter();
  return <TokenForm onSuccess={() => router.push("/chat")} />;
}
