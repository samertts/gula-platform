import { useQuery } from "@tanstack/react-query";
import { aiPlatformApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, Badge, Input, Button, Textarea } from "@/components/ui";
import { PageHeader, LoadingSpinner, ErrorDisplay, EmptyState } from "@/components/shared/PageComponents";
import { Brain, Search, Share2, Bot, MessageSquare } from "lucide-react";
import { useState, type FormEvent } from "react";

type Tab = "overview" | "search-rag" | "knowledge-graph" | "agent-tools" | "sessions";

export function AiPlatformPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const tabs: { key: Tab; label: string; icon: typeof Brain }[] = [
    { key: "overview", label: "نظرة عامة", icon: Brain },
    { key: "search-rag", label: "البحث و RAG", icon: Search },
    { key: "knowledge-graph", label: "المعرفة البيانية", icon: Share2 },
    { key: "agent-tools", label: "أدوات الوكلاء", icon: Bot },
    { key: "sessions", label: "الجلسات", icon: MessageSquare },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="منصة الذكاء الاصطناعي v2" description="إدارة وتشغيل خدمات الذكاء الاصطناعي المتقدمة" />

      <div className="flex gap-2 border-b pb-2 overflow-x-auto">
        {tabs.map(({ key, label, icon: Icon }) => (
          <Button key={key} variant={activeTab === key ? "default" : "ghost"} size="sm" onClick={() => setActiveTab(key)}>
            <Icon className="h-4 w-4" />
            {label}
          </Button>
        ))}
      </div>

      {activeTab === "overview" && <OverviewTab />}
      {activeTab === "search-rag" && <SearchRagTab />}
      {activeTab === "knowledge-graph" && <KnowledgeGraphTab />}
      {activeTab === "agent-tools" && <AgentToolsTab />}
      {activeTab === "sessions" && <SessionsTab />}
    </div>
  );
}

function OverviewTab() {
  const metrics = useQuery({ queryKey: ["ai-metrics"], queryFn: () => aiPlatformApi.metrics() });
  const governanceModels = useQuery({ queryKey: ["ai-governance-models"], queryFn: () => aiPlatformApi.governanceModels() });
  const governancePrompts = useQuery({ queryKey: ["ai-governance-prompts"], queryFn: () => aiPlatformApi.governancePrompts() });

  if (metrics.isLoading || governanceModels.isLoading || governancePrompts.isLoading) return <LoadingSpinner />;
  if (metrics.error) return <ErrorDisplay error={metrics.error?.toString()} onRetry={() => metrics.refetch()} />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader><CardTitle>إجمالي الطلبات</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{(metrics.data as any)?.total_requests ?? "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>معدل النجاح</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{(metrics.data as any)?.success_rate ?? "—"}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>متوسط وقت الاستجابة</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{(metrics.data as any)?.avg_latency_ms ?? "—"}ms</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>الطلبات اليوم</CardTitle></CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{(metrics.data as any)?.today_requests ?? "—"}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>نماذج الحوكمة</CardTitle></CardHeader>
          <CardContent>
            {governanceModels.error ? (
              <p className="text-sm text-destructive">خطأ في تحميل البيانات</p>
            ) : (
              <>
                <p className="text-3xl font-bold">
                  {Array.isArray(governanceModels.data) ? governanceModels.data.length : (governanceModels.data as any)?.total ?? (governanceModels.data as any)?.count ?? "—"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">نموذج حوكمة مسجل</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>القوالب النصية</CardTitle></CardHeader>
          <CardContent>
            {governancePrompts.error ? (
              <p className="text-sm text-destructive">خطأ في تحميل البيانات</p>
            ) : (
              <>
                <p className="text-3xl font-bold">
                  {Array.isArray(governancePrompts.data) ? governancePrompts.data.length : (governancePrompts.data as any)?.total ?? (governancePrompts.data as any)?.count ?? "—"}
                </p>
                <p className="text-sm text-muted-foreground mt-1">قالب نصي معتمد</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function SearchRagTab() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchData, setSearchData] = useState<Record<string, unknown> | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [ragQuery, setRagQuery] = useState("");
  const [ragResponse, setRagResponse] = useState<Record<string, unknown> | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState<string | null>(null);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setSearchError(null);
    try {
      const res = await aiPlatformApi.search({ query: searchQuery });
      setSearchData(res);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "حدث خطأ في البحث");
    } finally {
      setSearchLoading(false);
    }
  };

  const handleRag = async (e: FormEvent) => {
    e.preventDefault();
    if (!ragQuery.trim()) return;
    setRagLoading(true);
    setRagError(null);
    try {
      const res = await aiPlatformApi.ragQuery({ query: ragQuery });
      setRagResponse(res);
    } catch (err) {
      setRagError(err instanceof Error ? err.message : "حدث خطأ في الاستعلام");
    } finally {
      setRagLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>البحث الدلالي</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input
              placeholder="أدخل مصطلح البحث..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              dir="auto"
            />
            <Button type="submit" loading={searchLoading}><Search className="h-4 w-4" />بحث</Button>
          </form>

          {searchError && <p className="text-sm text-destructive">{searchError}</p>}

          {searchLoading && <LoadingSpinner />}

          {searchData && !searchLoading && (
            <div className="space-y-3">
              <h4 className="font-medium">نتائج البحث:</h4>
              {Array.isArray((searchData as any)?.results) && (searchData as any).results.length === 0 ? (
                <EmptyState icon={Search} title="لا توجد نتائج" description="لم يتم العثور على نتائج للبحث" />
              ) : (
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(searchData, null, 2)}
                </pre>
              )}
            </div>
          )}

          {!searchData && !searchLoading && !searchError && (
            <EmptyState icon={Search} title="البحث الدلالي" description="أدخل استعلام البحث للبدء" />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>استعلام RAG</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleRag} className="flex gap-2">
            <Textarea
              placeholder="أدخل سؤالك للاستعلام من المستندات..."
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              dir="auto"
            />
            <Button type="submit" loading={ragLoading}><Bot className="h-4 w-4" />استعلام</Button>
          </form>

          {ragError && <p className="text-sm text-destructive">{ragError}</p>}

          {ragLoading && <LoadingSpinner />}

          {ragResponse && !ragLoading && (
            <div className="space-y-3">
              <h4 className="font-medium">الرد:</h4>
              <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(ragResponse, null, 2)}
              </pre>
            </div>
          )}

          {!ragResponse && !ragLoading && !ragError && (
            <EmptyState icon={Bot} title="استعلام RAG" description="اطرح سؤالاً للاستعلام من قاعدة المعرفة" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function KnowledgeGraphTab() {
  const kgInfo = useQuery({ queryKey: ["kg-info"], queryFn: () => aiPlatformApi.knowledgeGraphInfo() });
  const [nodeQuery, setNodeQuery] = useState("");
  const [nodeResults, setNodeResults] = useState<Record<string, unknown> | null>(null);
  const [nodeLoading, setNodeLoading] = useState(false);
  const [nodeError, setNodeError] = useState<string | null>(null);

  const handleNodeSearch = async (e: FormEvent) => {
    e.preventDefault();
    if (!nodeQuery.trim()) return;
    setNodeLoading(true);
    setNodeError(null);
    try {
      const res = await aiPlatformApi.knowledgeGraphSearch({ query: nodeQuery });
      setNodeResults(res);
    } catch (err) {
      setNodeError(err instanceof Error ? err.message : "حدث خطأ في البحث");
    } finally {
      setNodeLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>إحصائيات المعرفة البيانية</CardTitle></CardHeader>
        <CardContent>
          {kgInfo.isLoading ? (
            <LoadingSpinner />
          ) : kgInfo.error ? (
            <ErrorDisplay onRetry={() => kgInfo.refetch()} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">العقد</p>
                <p className="text-2xl font-bold">{(kgInfo.data as any)?.nodes ?? (kgInfo.data as any)?.node_count ?? "—"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">العلاقات</p>
                <p className="text-2xl font-bold">{(kgInfo.data as any)?.edges ?? (kgInfo.data as any)?.edge_count ?? (kgInfo.data as any)?.relationships ?? "—"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">أنواع العقد</p>
                <p className="text-2xl font-bold">{(kgInfo.data as any)?.node_types ?? "—"}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>بحث العقد</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleNodeSearch} className="flex gap-2">
            <Input
              placeholder="ابحث عن عقدة..."
              value={nodeQuery}
              onChange={(e) => setNodeQuery(e.target.value)}
              dir="auto"
            />
            <Button type="submit" loading={nodeLoading}><Search className="h-4 w-4" />بحث</Button>
          </form>

          {nodeError && <p className="text-sm text-destructive">{nodeError}</p>}

          {nodeLoading && <LoadingSpinner />}

          {nodeResults && !nodeLoading && (
            <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(nodeResults, null, 2)}
            </pre>
          )}

          {!nodeResults && !nodeLoading && !nodeError && (
            <EmptyState icon={Share2} title="بحث العقد" description="ابحث عن عقد في قاعدة المعرفة البيانية" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AgentToolsTab() {
  const tools = useQuery({ queryKey: ["agent-tools"], queryFn: () => aiPlatformApi.agentTools() });
  const [executeInput, setExecuteInput] = useState("");
  const [toolName, setToolName] = useState("");
  const [execResult, setExecResult] = useState<Record<string, unknown> | null>(null);
  const [execLoading, setExecLoading] = useState(false);
  const [execError, setExecError] = useState<string | null>(null);

  const handleExecute = async (e: FormEvent) => {
    e.preventDefault();
    if (!toolName.trim()) return;
    setExecLoading(true);
    setExecError(null);
    try {
      const payload: Record<string, unknown> = { tool: toolName, input: executeInput };
      try {
        payload.input = JSON.parse(executeInput);
      } catch {
        payload.input = executeInput;
      }
      const res = await aiPlatformApi.agentExecute(payload);
      setExecResult(res);
    } catch (err) {
      setExecError(err instanceof Error ? err.message : "حدث خطأ في التنفيذ");
    } finally {
      setExecLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>أدوات الوكلاء</CardTitle></CardHeader>
        <CardContent>
          {tools.isLoading ? (
            <LoadingSpinner />
          ) : tools.error ? (
            <ErrorDisplay onRetry={() => tools.refetch()} />
          ) : (
            <div className="space-y-3">
              {Array.isArray(tools.data) && tools.data.length === 0 ? (
                <EmptyState icon={Bot} title="لا توجد أدوات" description="لم يتم العثور على أدوات وكلاء" />
              ) : (
                <div className="grid gap-3">
                  {(Array.isArray(tools.data) ? tools.data : ((tools.data as Record<string, unknown>)?.tools as unknown[]) ?? []).map((t: unknown, idx: number) => {
                    const tool = t as Record<string, unknown>;
                    const name = (tool.name as string) || (tool.tool_name as string) || (tool.id as string) || `أداة ${idx + 1}`;
                    const desc = (tool.description as string) || (tool.desc as string) || "";
                    const active = !!(tool.enabled || tool.active);
                    return <div key={idx} className="flex items-center justify-between border-b pb-3 last:border-0"><div><p className="font-medium">{name}</p><p className="text-sm text-muted-foreground">{desc}</p></div><Badge variant={active ? "success" : "secondary"}>{active ? "مفعل" : "غير مفعل"}</Badge></div>;
                  })}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>تنفيذ وكيل</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleExecute} className="space-y-3">
            <Input
              placeholder="اسم الأداة (مثل: analyze_results)"
              value={toolName}
              onChange={(e) => setToolName(e.target.value)}
              dir="auto"
            />
            <Textarea
              placeholder="بيانات الإدخال (JSON أو نص)"
              value={executeInput}
              onChange={(e) => setExecuteInput(e.target.value)}
              dir="auto"
            />
            <Button type="submit" loading={execLoading}><Bot className="h-4 w-4" />تنفيذ</Button>
          </form>

          {execError && <p className="text-sm text-destructive">{execError}</p>}

          {execLoading && <LoadingSpinner />}

          {execResult && !execLoading && (
            <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(execResult, null, 2)}
            </pre>
          )}

          {!execResult && !execLoading && !execError && (
            <EmptyState icon={Bot} title="تنفيذ وكيل" description="اختر أداة وأدخل البيانات للتنفيذ" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SessionsTab() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [sending, setSending] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const handleCreateSession = async () => {
    setCreating(true);
    setSessionError(null);
    try {
      const res = await aiPlatformApi.createSession();
      const newId = (res as Record<string, unknown>)?.session_id as string || (res as Record<string, unknown>)?.id as string || (res as Record<string, unknown>)?.sessionId as string;
      setSessionId(newId);
      setMessages([]);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "حدث خطأ في إنشاء الجلسة");
    } finally {
      setCreating(false);
    }
  };

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !sessionId) return;
    setSending(true);
    setSessionError(null);
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    const msg = message;
    setMessage("");
    try {
      const res = await aiPlatformApi.sessionMessage({ session_id: sessionId, message: msg });
      const reply = (res as Record<string, unknown>)?.response || (res as Record<string, unknown>)?.reply || (res as Record<string, unknown>)?.message || JSON.stringify(res);
      setMessages((prev) => [...prev, { role: "assistant", content: typeof reply === "string" ? reply : JSON.stringify(reply) }]);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "حدث خطأ في إرسال الرسالة");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>جلسة المحادثة</CardTitle>
            <Button onClick={handleCreateSession} loading={creating} size="sm">
              <MessageSquare className="h-4 w-4" />
              جلسة جديدة
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {sessionError && <p className="text-sm text-destructive">{sessionError}</p>}

          {!sessionId ? (
            <EmptyState icon={MessageSquare} title="لا توجد جلسة" description="أنشئ جلسة جديدة لبدء المحادثة" action={{ label: "إنشاء جلسة", onClick: handleCreateSession }} />
          ) : (
            <>
              <div className="flex items-center gap-2">
                <Badge variant="success">معرف الجلسة: {sessionId}</Badge>
              </div>

              <div className="bg-muted rounded-lg p-4 max-h-96 overflow-y-auto space-y-3" dir="auto">
                {messages.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">أرسل رسالة لبدء المحادثة</p>
                ) : (
                  messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === "user" ? "justify-start" : "justify-end"}`}>
                      <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-background border"}`}>
                        <p className="text-xs opacity-70 mb-1">{msg.role === "user" ? "أنت" : "المساعد"}</p>
                        <p>{msg.content}</p>
                      </div>
                    </div>
                  ))
                )}
                {sending && (
                  <div className="flex justify-end">
                    <div className="bg-background border rounded-lg px-4 py-2 text-sm">
                      <LoadingSpinner />
                    </div>
                  </div>
                )}
              </div>

              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  placeholder="اكتب رسالتك..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  dir="auto"
                />
                <Button type="submit" loading={sending} disabled={!message.trim()}>
                  إرسال
                </Button>
              </form>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
