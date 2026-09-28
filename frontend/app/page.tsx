import { redirect } from "next/navigation";

// The dashboard sends visitors who aren't logged in on to /login.
export default function Home() {
  redirect("/dashboard");
}
