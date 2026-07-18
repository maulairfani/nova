import { Suspense } from "react";
import { ChatWindow } from "../components/ChatWindow";

export default function Home() {
  return (
    <Suspense fallback={null}>
      <ChatWindow />
    </Suspense>
  );
}
