import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../../app/providers/AuthProvider";
import { useAdminClientDetail, useAdminClients } from "../../../domain/hooks/useAdminClients";
import { useAdminMetrics } from "../../../domain/hooks/useAdminMetrics";
import { useAdminMentors } from "../../../domain/hooks/useAdminMentors";
import { useAdminPillars } from "../../../domain/hooks/useAdminPillars";
import { useAdminProducts } from "../../../domain/hooks/useAdminProducts";
import { useAdminStudentRadar, useAdminStudents } from "../../../domain/hooks/useAdminStudents";
import { createAdminClient } from "../../../domain/services/adminClientService";
import { createAdminMetric, listAdminMetricsByProduct } from "../../../domain/services/adminMetricService";
import { createAdminMentor } from "../../../domain/services/adminMentorService";
import { createAdminPillar } from "../../../domain/services/adminPillarService";
import { createAdminProduct } from "../../../domain/services/adminProductService";
import { createAdminStudent, loadAdminStudentIndicators, reassignAdminStudent, unlinkAdminStudent } from "../../../domain/services/adminStudentService";
import { listDatabaseRecords, listDatabaseTables, updateDatabaseRecord } from "../../../domain/services/adminDatabaseViewService";
import { executeAdminApiOperation, listAdminApiOperations, type AdminApiOperationItem, type AdminApiOperationExecution } from "../../../domain/services/adminApiOperationsService";
import type { AdminMetricDirection, AdminMetricDto } from "../../../contracts/adminMetric";
import { toUserErrorMessage } from "../../../shared/api/types";
import { AdminShell } from "../components/AdminShell";
import "../admin.css";

type CreateModalStep = "form" | "confirm" | "success";
type CreateTarget = "cliente" | "produto" | "mentor" | "pilar" | "metrica" | "aluno";
type StudentLinkMode = "reassign" | "unlink";

type IndicatorMetricRow = {
  metric_id: string;
  name: string;
  pillar_name?: string;
  unit: string;
  baseline: string;
  current: string;
  projected: string;
  improving_trend: boolean;
};

type EditableCommandCenterRow = {
  progress: string;
  engagement: string;
  daysLeft: string;
};

type EditableMatrixRow = {
  urgency: "normal" | "watch" | "critical" | "rescue";
  progress: string;
  engagement: string;
  daysLeft: string;
  ltv: string;
};

type EditableRadarRow = {
  baseline: string;
  current: string;
  projected: string;
};

type EditableProviderMetricRow = {
  name: string;
  code: string;
  unit: string;
  direction: AdminMetricDirection;
};

type OperationalViewMode = "provider" | "client";
type ProviderRadarTab = "pillars" | "metrics";

const CREATE_OPTIONS: Array<{ key: CreateTarget; label: string }> = [
  { key: "cliente", label: "Cliente" },
  { key: "produto", label: "Produto" },
  { key: "mentor", label: "Mentor" },
  { key: "pilar", label: "Pilar" },
  { key: "metrica", label: "Metrica" },
  { key: "aluno", label: "Aluno" }
];

const URGENCY_OPTIONS: Array<{ value: EditableMatrixRow["urgency"]; label: string }> = [
  { value: "normal", label: "Estável" },
  { value: "watch", label: "Atenção" },
  { value: "critical", label: "Crítico" },
  { value: "rescue", label: "Resgate" }
];

const METRIC_DIRECTION_OPTIONS: Array<{ value: AdminMetricDirection; label: string }> = [
  { value: "higher_better", label: "Maior melhor" },
  { value: "lower_better", label: "Menor melhor" },
  { value: "target_range", label: "Faixa alvo" }
];

function formatCnpj(value: string) {
  const digits = value.replace(/\D+/g, "").slice(0, 14);
  if (digits.length !== 14) {
    return value;
  }
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function formatCpf(value: string) {
  const digits = value.replace(/\D+/g, "").slice(0, 11);
  if (digits.length !== 11) {
    return value;
  }
  return digits.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
}

function formatDatabaseCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function shouldHideDatabaseColumn(tableName: string, columnName: string): boolean {
  const normalizedTable = tableName.trim().toLowerCase();
  const normalizedColumn = columnName.trim().toLowerCase();
  if (normalizedColumn === "hash") {
    return true;
  }
  if ((normalizedTable === "contact_users_v2" || normalizedTable === "users") && normalizedColumn.endsWith("_hash")) {
    return true;
  }
  return false;
}

function toPercentInput(value: number | null | undefined): string {
  const safe = Number.isFinite(value) ? Number(value) : 0;
  const normalized = safe > 1 ? safe / 100 : safe;
  return (Math.max(0, Math.min(1, normalized)) * 100).toFixed(1);
}

const EMPTY_CLIENT_FORM = {
  name: "",
  brand_name: "",
  cnpj: "",
  slug: "",
  timezone: "America/Sao_Paulo",
  currency: "BRL",
  notes: ""
};

const EMPTY_PRODUCT_FORM = {
  name: "",
  code: "",
  slug: "",
  description: "",
  delivery_model: "live"
};

const EMPTY_MENTOR_FORM = {
  full_name: "",
  cpf: "",
  email: "",
  phone: "",
  bio: "",
  notes: ""
};

const EMPTY_STUDENT_FORM = {
  full_name: "",
  cpf: "",
  email: "",
  phone: "",
  notes: ""
};

const EMPTY_PILLAR_FORM = {
  name: "",
  code: "",
  order_index: "1"
};

const EMPTY_METRIC_FORM: {
  name: string;
  code: string;
  direction: "higher_better" | "lower_better" | "target_range";
  unit: string;
} = {
  name: "",
  code: "",
  direction: "higher_better",
  unit: "%"
};

const EMPTY_CHECKPOINT_FORM = {
  week: "1",
  status: "green" as const,
  label: "Inicio consistente"
};

export function AdminPage() {
  const { authReady, isAuthenticated, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const canLoadAdmin = authReady && isAuthenticated && user?.role === "admin";
  const clientsResource = useAdminClients(canLoadAdmin);

  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [selectedMentorId, setSelectedMentorId] = useState<string | null>(null);
  const [selectedPillarId, setSelectedPillarId] = useState<string | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [isCreateChooserOpen, setIsCreateChooserOpen] = useState(false);
  const [createChooserMessage, setCreateChooserMessage] = useState<string | null>(null);
  const [isPillarExpanded, setIsPillarExpanded] = useState(false);

  const [selectedProviderId, setSelectedProviderId] = useState<string>("");
  const [providerSearchMentorId, setProviderSearchMentorId] = useState<string | null>(null);
  const [providerStudentsPage, setProviderStudentsPage] = useState(1);
  const [selectedClientViewClientId, setSelectedClientViewClientId] = useState<string>("");
  const [commandCenterDrafts, setCommandCenterDrafts] = useState<Record<string, EditableCommandCenterRow>>({});
  const [matrixDrafts, setMatrixDrafts] = useState<Record<string, EditableMatrixRow>>({});
  const [radarDrafts, setRadarDrafts] = useState<Record<string, EditableRadarRow>>({});
  const [providerRadarTab, setProviderRadarTab] = useState<ProviderRadarTab>("pillars");
  const [providerMetricDrafts, setProviderMetricDrafts] = useState<Record<string, EditableProviderMetricRow>>({});

  const activePanel = searchParams.get("panel");
  const isClientsPanel = activePanel === "clientes";
  const isProviderPanel = activePanel === "provider";
  const isClientViewPanel = activePanel === "client";
  const isProductsPanel = activePanel === "produtos";
  const isMentorsPanel = activePanel === "mentores";
  const isStudentsPanel = activePanel === "alunos";
  const isDatabasePanel = activePanel === "database";
  const isApiPanel = activePanel === "api";
  const hasContextPanel = isClientsPanel || isProductsPanel || isMentorsPanel || isStudentsPanel || isDatabasePanel || isProviderPanel || isClientViewPanel;
  const hasProductContextPanel = isProductsPanel || isMentorsPanel || isStudentsPanel || isProviderPanel || isClientViewPanel;
  const shouldLoadStudents = isStudentsPanel || isProviderPanel || isClientViewPanel;
  const showClientSectionBar = !hasContextPanel;

  const clientDetailResource = useAdminClientDetail(canLoadAdmin ? selectedClientId : null, canLoadAdmin);
  const productsResource = useAdminProducts(canLoadAdmin && hasContextPanel ? selectedClientId : null);
  const mentorsResource = useAdminMentors(canLoadAdmin && hasProductContextPanel ? selectedProductId : null);
  const pillarsResource = useAdminPillars(canLoadAdmin && hasProductContextPanel ? selectedProductId : null);
  const shouldLoadAdminMetrics = canLoadAdmin && (isProductsPanel || (isProviderPanel && providerRadarTab === "metrics"));
  const metricsResource = useAdminMetrics(shouldLoadAdminMetrics ? selectedPillarId : null);
  const studentsMentorId = canLoadAdmin && shouldLoadStudents
    ? (isProviderPanel ? providerSearchMentorId : selectedMentorId)
    : null;
  const studentsResource = useAdminStudents(studentsMentorId);
  const clientViewRadarResource = useAdminStudentRadar(selectedMentorId, selectedStudentId);

  const providerStudentsPageSize = 10;
  const providerStudentsTotalPages = Math.max(1, Math.ceil(studentsResource.data.length / providerStudentsPageSize));
  const providerVisibleStudents = useMemo(() => {
    const start = (providerStudentsPage - 1) * providerStudentsPageSize;
    return studentsResource.data.slice(start, start + providerStudentsPageSize);
  }, [providerStudentsPage, studentsResource.data]);

  const [clientFormState, setClientFormState] = useState(EMPTY_CLIENT_FORM);
  const [clientFormError, setClientFormError] = useState<string | null>(null);
  const [clientSubmitting, setClientSubmitting] = useState(false);
  const [isClientModalOpen, setIsClientModalOpen] = useState(false);
  const [clientModalStep, setClientModalStep] = useState<CreateModalStep>("form");
  const clientCloseTimeoutRef = useRef<number | null>(null);

  const [productFormState, setProductFormState] = useState(EMPTY_PRODUCT_FORM);
  const [productFormError, setProductFormError] = useState<string | null>(null);
  const [productSubmitting, setProductSubmitting] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [productModalStep, setProductModalStep] = useState<CreateModalStep>("form");
  const productCloseTimeoutRef = useRef<number | null>(null);

  const [mentorFormState, setMentorFormState] = useState(EMPTY_MENTOR_FORM);
  const [mentorFormError, setMentorFormError] = useState<string | null>(null);
  const [mentorSubmitting, setMentorSubmitting] = useState(false);
  const [isMentorModalOpen, setIsMentorModalOpen] = useState(false);
  const [mentorModalStep, setMentorModalStep] = useState<CreateModalStep>("form");
  const mentorCloseTimeoutRef = useRef<number | null>(null);

  const [studentFormState, setStudentFormState] = useState(EMPTY_STUDENT_FORM);
  const [studentFormError, setStudentFormError] = useState<string | null>(null);
  const [studentSubmitting, setStudentSubmitting] = useState(false);
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [studentModalStep, setStudentModalStep] = useState<CreateModalStep>("form");
  const studentCloseTimeoutRef = useRef<number | null>(null);
  const [studentLinkMode, setStudentLinkMode] = useState<StudentLinkMode>("reassign");
  const [studentLinkJustification, setStudentLinkJustification] = useState("");
  const [studentLinkTargetMentorId, setStudentLinkTargetMentorId] = useState<string>("");
  const [studentLinkError, setStudentLinkError] = useState<string | null>(null);
  const [studentLinkSubmitting, setStudentLinkSubmitting] = useState(false);
  const [isStudentLinkModalOpen, setIsStudentLinkModalOpen] = useState(false);
  const [studentLinkModalStep, setStudentLinkModalStep] = useState<CreateModalStep>("form");
  const studentLinkCloseTimeoutRef = useRef<number | null>(null);
  const [isIndicatorLoadModalOpen, setIsIndicatorLoadModalOpen] = useState(false);
  const [indicatorLoadModalStep, setIndicatorLoadModalStep] = useState<CreateModalStep>("form");
  const [indicatorMetricRows, setIndicatorMetricRows] = useState<IndicatorMetricRow[]>([]);
  const [indicatorCheckpointForm, setIndicatorCheckpointForm] = useState(EMPTY_CHECKPOINT_FORM);
  const [indicatorCatalogLoading, setIndicatorCatalogLoading] = useState(false);
  const [indicatorCatalogError, setIndicatorCatalogError] = useState<string | null>(null);
  const [indicatorLoadError, setIndicatorLoadError] = useState<string | null>(null);
  const [indicatorLoadSubmitting, setIndicatorLoadSubmitting] = useState(false);
  const indicatorLoadCloseTimeoutRef = useRef<number | null>(null);

  const [pillarFormState, setPillarFormState] = useState(EMPTY_PILLAR_FORM);
  const [pillarFormError, setPillarFormError] = useState<string | null>(null);
  const [pillarSubmitting, setPillarSubmitting] = useState(false);
  const [isPillarModalOpen, setIsPillarModalOpen] = useState(false);
  const [pillarModalStep, setPillarModalStep] = useState<CreateModalStep>("form");
  const pillarCloseTimeoutRef = useRef<number | null>(null);

  const [metricFormState, setMetricFormState] = useState(EMPTY_METRIC_FORM);
  const [metricFormError, setMetricFormError] = useState<string | null>(null);
  const [metricSubmitting, setMetricSubmitting] = useState(false);
  const [isMetricModalOpen, setIsMetricModalOpen] = useState(false);
  const [metricModalStep, setMetricModalStep] = useState<CreateModalStep>("form");
  const metricCloseTimeoutRef = useRef<number | null>(null);

  const [databaseTables, setDatabaseTables] = useState<string[]>([]);
  const [selectedDatabaseTable, setSelectedDatabaseTable] = useState<string>("");
  const [databaseRows, setDatabaseRows] = useState<Array<Record<string, unknown>>>([]);
  const [databaseOffset, setDatabaseOffset] = useState(0);
  const [databaseTotal, setDatabaseTotal] = useState(0);
  const [databaseLoading, setDatabaseLoading] = useState(false);
  const [databaseError, setDatabaseError] = useState<string | null>(null);

  const [apiCatalog, setApiCatalog] = useState<AdminApiOperationItem[]>([]);
  const [apiCatalogLoading, setApiCatalogLoading] = useState(false);
  const [apiCatalogError, setApiCatalogError] = useState<string | null>(null);
  const [apiExecutionStatusByEndpoint, setApiExecutionStatusByEndpoint] = useState<Record<string, string>>({});


  const activeClients = useMemo(() => clientsResource.data.filter((item) => item.is_active), [clientsResource.data]);
  const selectedClient = clientDetailResource.data;
  const selectedProduct = useMemo(() => {
    if (!selectedProductId) {
      return null;
    }
    return productsResource.data.find((item) => item.id === selectedProductId) ?? null;
  }, [productsResource.data, selectedProductId]);
  const selectedMentor = useMemo(() => {
    if (mentorsResource.data.length === 0) {
      return null;
    }
    if (selectedMentorId) {
      return mentorsResource.data.find((item) => item.id === selectedMentorId) ?? mentorsResource.data[0];
    }
    if (selectedProduct?.mentor_id) {
      return mentorsResource.data.find((item) => item.id === selectedProduct.mentor_id) ?? mentorsResource.data[0];
    }
    return mentorsResource.data[0];
  }, [mentorsResource.data, selectedMentorId, selectedProduct?.mentor_id]);
  const selectedPillar = useMemo(() => {
    if (!selectedPillarId) {
      return null;
    }
    return pillarsResource.data.find((item) => item.id === selectedPillarId) ?? null;
  }, [pillarsResource.data, selectedPillarId]);
  const selectedStudent = useMemo(() => {
    if (!selectedStudentId) {
      return null;
    }
    return studentsResource.data.find((item) => item.id === selectedStudentId) ?? null;
  }, [studentsResource.data, selectedStudentId]);
  const availableMentorsForRelink = useMemo(
    () => mentorsResource.data.filter((item) => item.id !== selectedMentorId),
    [mentorsResource.data, selectedMentorId]
  );

  const pillarCards = useMemo<Array<{ id: string; label: string; title: string; detail: string }>>(
    () =>
      pillarsResource.data.map((pillar, index) => ({
        id: pillar.id,
        label: `Pilar ${index + 1}`,
        title: pillar.name,
        detail: pillar.code.toUpperCase()
      })),
    [pillarsResource.data]
  );

  const databaseColumns = useMemo(() => {
    const columns = new Set<string>();
    databaseRows.forEach((row) => {
      Object.keys(row).forEach((column) => columns.add(column));
    });
    return Array.from(columns).filter((column) => !shouldHideDatabaseColumn(selectedDatabaseTable, column));
  }, [databaseRows, selectedDatabaseTable]);

  useEffect(() => {
    if (activeClients.length === 0) {
      if (selectedClientId !== null) {
        setSelectedClientId(null);
      }
      return;
    }
    if (!activeClients.some((item) => item.id === selectedClientId)) {
      setSelectedClientId(activeClients[0].id);
    }
  }, [activeClients, selectedClientId]);

  useEffect(() => {
    if (!isClientViewPanel) {
      return;
    }
    if (activeClients.length === 0) {
      if (selectedClientViewClientId) {
        setSelectedClientViewClientId("");
      }
      return;
    }
    if (!activeClients.some((item) => item.id === selectedClientViewClientId)) {
      setSelectedClientViewClientId(selectedClientId ?? activeClients[0].id);
    }
  }, [activeClients, isClientViewPanel, selectedClientId, selectedClientViewClientId]);

  useEffect(() => {
    if (!isClientViewPanel || !selectedClientViewClientId) {
      return;
    }
    if (selectedClientViewClientId !== selectedClientId) {
      setSelectedClientId(selectedClientViewClientId);
    }
  }, [isClientViewPanel, selectedClientId, selectedClientViewClientId]);

  useEffect(() => {
    if (!hasContextPanel || productsResource.data.length === 0) {
      if (selectedProductId !== null) {
        setSelectedProductId(null);
      }
      if (selectedMentorId !== null) {
        setSelectedMentorId(null);
      }
      if (selectedStudentId !== null) {
        setSelectedStudentId(null);
      }
      if (selectedPillarId !== null) {
        setSelectedPillarId(null);
      }
      setIsPillarExpanded(false);
      return;
    }
    if (!productsResource.data.some((item) => item.id === selectedProductId)) {
      setSelectedProductId(productsResource.data[0].id);
    }
  }, [hasContextPanel, productsResource.data, selectedMentorId, selectedPillarId, selectedProductId, selectedStudentId]);

  useEffect(() => {
    if (!hasProductContextPanel || mentorsResource.data.length === 0) {
      if (selectedMentorId !== null) {
        setSelectedMentorId(null);
      }
      return;
    }
    if (!mentorsResource.data.some((item) => item.id === selectedMentorId)) {
      const fallbackId = selectedProduct?.mentor_id ?? mentorsResource.data[0].id;
      setSelectedMentorId(fallbackId);
    }
  }, [hasProductContextPanel, mentorsResource.data, selectedMentorId, selectedProduct?.mentor_id]);

  useEffect(() => {
    if (!isProviderPanel) {
      return;
    }
    if (mentorsResource.data.length === 0) {
      if (selectedProviderId) {
        setSelectedProviderId("");
      }
      return;
    }
    if (!mentorsResource.data.some((item) => item.id === selectedProviderId)) {
      setSelectedProviderId(selectedMentor?.id ?? mentorsResource.data[0].id);
    }
  }, [isProviderPanel, mentorsResource.data, selectedMentor?.id, selectedProviderId]);

  useEffect(() => {
    if (!isProviderPanel || !selectedProviderId) {
      return;
    }
    if (selectedProviderId !== selectedMentorId) {
      setSelectedMentorId(selectedProviderId);
    }
  }, [isProviderPanel, selectedMentorId, selectedProviderId]);

  useEffect(() => {
    if (!isProviderPanel) {
      if (providerSearchMentorId !== null) {
        setProviderSearchMentorId(null);
      }
      return;
    }
    if (!selectedClientId || !selectedProductId || !selectedProviderId) {
      if (providerSearchMentorId !== null) {
        setProviderSearchMentorId(null);
      }
      return;
    }
    if (providerSearchMentorId && providerSearchMentorId !== selectedProviderId) {
      setProviderSearchMentorId(null);
    }
  }, [isProviderPanel, providerSearchMentorId, selectedClientId, selectedProductId, selectedProviderId]);

  useEffect(() => {
    if (providerStudentsPage > providerStudentsTotalPages) {
      setProviderStudentsPage(providerStudentsTotalPages);
    }
  }, [providerStudentsPage, providerStudentsTotalPages]);

  useEffect(() => {
    if (!(isStudentsPanel || isProviderPanel || isClientViewPanel) || studentsResource.data.length === 0) {
      if (selectedStudentId !== null) {
        setSelectedStudentId(null);
      }
      return;
    }
    if (!studentsResource.data.some((item) => item.id === selectedStudentId)) {
      setSelectedStudentId(studentsResource.data[0].id);
    }
  }, [isClientViewPanel, isProviderPanel, isStudentsPanel, selectedStudentId, studentsResource.data]);

  function handleProviderSearchStudents() {
    if (!selectedClientId || !selectedProductId || !selectedProviderId) {
      return;
    }
    setProviderStudentsPage(1);
    if (providerSearchMentorId === selectedProviderId) {
      void studentsResource.refresh();
      return;
    }
    setProviderSearchMentorId(selectedProviderId);
  }

  useEffect(() => {
    setIsPillarExpanded(false);
  }, [selectedProductId]);

  useEffect(() => {
    if (!hasProductContextPanel || pillarsResource.data.length === 0) {
      if (selectedPillarId !== null) {
        setSelectedPillarId(null);
      }
      return;
    }
    if (!pillarsResource.data.some((item) => item.id === selectedPillarId)) {
      setSelectedPillarId(pillarsResource.data[0].id);
    }
  }, [hasProductContextPanel, pillarsResource.data, selectedPillarId]);

  useEffect(() => {
    if (!isProviderPanel) {
      if (providerRadarTab !== "pillars") {
        setProviderRadarTab("pillars");
      }
      return;
    }
    const radarPillarIds = clientViewRadarResource.data.axisScores
      .map((axis) => axis.axisId)
      .filter((axisId): axisId is string => Boolean(axisId));
    if (radarPillarIds.length === 0) {
      return;
    }
    if (!selectedPillarId || !radarPillarIds.includes(selectedPillarId)) {
      setSelectedPillarId(radarPillarIds[0]);
    }
  }, [clientViewRadarResource.data.axisScores, isProviderPanel, providerRadarTab, selectedPillarId]);

  useEffect(() => {
    setIsCreateChooserOpen(false);
    setCreateChooserMessage(null);
  }, [activePanel, selectedClientId, selectedProductId, selectedPillarId, selectedStudentId]);

  useEffect(() => {
    return () => {
      if (clientCloseTimeoutRef.current !== null) {
        window.clearTimeout(clientCloseTimeoutRef.current);
      }
      if (productCloseTimeoutRef.current !== null) {
        window.clearTimeout(productCloseTimeoutRef.current);
      }
      if (mentorCloseTimeoutRef.current !== null) {
        window.clearTimeout(mentorCloseTimeoutRef.current);
      }
      if (studentCloseTimeoutRef.current !== null) {
        window.clearTimeout(studentCloseTimeoutRef.current);
      }
      if (pillarCloseTimeoutRef.current !== null) {
        window.clearTimeout(pillarCloseTimeoutRef.current);
      }
      if (metricCloseTimeoutRef.current !== null) {
        window.clearTimeout(metricCloseTimeoutRef.current);
      }
      if (studentLinkCloseTimeoutRef.current !== null) {
        window.clearTimeout(studentLinkCloseTimeoutRef.current);
      }
      if (indicatorLoadCloseTimeoutRef.current !== null) {
        window.clearTimeout(indicatorLoadCloseTimeoutRef.current);
      }
    };
  }, []);

  function closeCreateChooser() {
    setIsCreateChooserOpen(false);
    setCreateChooserMessage(null);
  }

  function toggleCreateChooser() {
    setCreateChooserMessage(null);
    setIsCreateChooserOpen((current) => !current);
  }

  function resetClientModalState() {
    setClientFormError(null);
    setClientSubmitting(false);
    setClientModalStep("form");
  }

  function closeClientCreateModal() {
    if (clientCloseTimeoutRef.current !== null) {
      window.clearTimeout(clientCloseTimeoutRef.current);
      clientCloseTimeoutRef.current = null;
    }
    setIsClientModalOpen(false);
    resetClientModalState();
  }

  function openClientCreateModal() {
    closeCreateChooser();
    setClientFormState(EMPTY_CLIENT_FORM);
    setIsClientModalOpen(true);
    resetClientModalState();
  }

  function resetProductModalState() {
    setProductFormError(null);
    setProductSubmitting(false);
    setProductModalStep("form");
  }

  function closeProductCreateModal() {
    if (productCloseTimeoutRef.current !== null) {
      window.clearTimeout(productCloseTimeoutRef.current);
      productCloseTimeoutRef.current = null;
    }
    setIsProductModalOpen(false);
    resetProductModalState();
  }

  function openProductCreateModal() {
    if (!selectedClientId) {
      return;
    }
    closeCreateChooser();
    setProductFormState(EMPTY_PRODUCT_FORM);
    setIsProductModalOpen(true);
    resetProductModalState();
  }

  function resetMentorModalState() {
    setMentorFormError(null);
    setMentorSubmitting(false);
    setMentorModalStep("form");
  }

  function closeMentorCreateModal() {
    if (mentorCloseTimeoutRef.current !== null) {
      window.clearTimeout(mentorCloseTimeoutRef.current);
      mentorCloseTimeoutRef.current = null;
    }
    setIsMentorModalOpen(false);
    resetMentorModalState();
  }

  function openMentorCreateModal() {
    if (!selectedProductId || !hasProductContextPanel) {
      return;
    }
    closeCreateChooser();
    setMentorFormState(EMPTY_MENTOR_FORM);
    setIsMentorModalOpen(true);
    resetMentorModalState();
  }

  function resetStudentModalState() {
    setStudentFormError(null);
    setStudentSubmitting(false);
    setStudentModalStep("form");
  }

  function closeStudentCreateModal() {
    if (studentCloseTimeoutRef.current !== null) {
      window.clearTimeout(studentCloseTimeoutRef.current);
      studentCloseTimeoutRef.current = null;
    }
    setIsStudentModalOpen(false);
    resetStudentModalState();
  }

  function resetStudentLinkModalState() {
    setStudentLinkError(null);
    setStudentLinkSubmitting(false);
    setStudentLinkModalStep("form");
  }

  function closeStudentLinkModal() {
    if (studentLinkCloseTimeoutRef.current !== null) {
      window.clearTimeout(studentLinkCloseTimeoutRef.current);
      studentLinkCloseTimeoutRef.current = null;
    }
    setIsStudentLinkModalOpen(false);
    resetStudentLinkModalState();
  }

  function openStudentLinkModal() {
    if (!selectedStudent) {
      return;
    }
    closeCreateChooser();
    const fallbackMentor = availableMentorsForRelink[0]?.id ?? "";
    setStudentLinkMode(fallbackMentor ? "reassign" : "unlink");
    setStudentLinkTargetMentorId(fallbackMentor);
    setStudentLinkJustification("");
    setIsStudentLinkModalOpen(true);
    resetStudentLinkModalState();
  }

  function resetIndicatorLoadModalState() {
    setIndicatorLoadError(null);
    setIndicatorCatalogError(null);
    setIndicatorLoadSubmitting(false);
    setIndicatorLoadModalStep("form");
  }

  function closeIndicatorLoadModal() {
    if (indicatorLoadCloseTimeoutRef.current !== null) {
      window.clearTimeout(indicatorLoadCloseTimeoutRef.current);
      indicatorLoadCloseTimeoutRef.current = null;
    }
    setIsIndicatorLoadModalOpen(false);
    resetIndicatorLoadModalState();
  }

  async function openIndicatorLoadModal() {
    if (!selectedStudent || !selectedProductId) {
      return;
    }
    closeCreateChooser();
    setIndicatorMetricRows([]);
    setIndicatorCheckpointForm(EMPTY_CHECKPOINT_FORM);
    setIndicatorCatalogLoading(true);
    setIndicatorCatalogError(null);
    setIndicatorLoadError(null);
    setIsIndicatorLoadModalOpen(true);
    setIndicatorLoadModalStep("form");

    try {
      const metrics = await listAdminMetricsByProduct(selectedProductId);
      setIndicatorMetricRows(
        metrics.map((metric) => ({
          metric_id: metric.id,
          name: metric.name,
          pillar_name: metric.pillar_name,
          unit: metric.unit || metric.code.toUpperCase(),
          baseline: "",
          current: "",
          projected: "",
          improving_trend: true
        }))
      );
    } catch (error) {
      setIndicatorCatalogError(toUserErrorMessage(error, "Falha ao carregar metricas do produto."));
    } finally {
      setIndicatorCatalogLoading(false);
    }
  }

  function openStudentCreateModal() {
    if (!selectedMentorId || !(isMentorsPanel || isStudentsPanel)) {
      return;
    }
    closeCreateChooser();
    setStudentFormState(EMPTY_STUDENT_FORM);
    setIsStudentModalOpen(true);
    resetStudentModalState();
  }

  function resetPillarModalState() {
    setPillarFormError(null);
    setPillarSubmitting(false);
    setPillarModalStep("form");
  }

  function closePillarCreateModal() {
    if (pillarCloseTimeoutRef.current !== null) {
      window.clearTimeout(pillarCloseTimeoutRef.current);
      pillarCloseTimeoutRef.current = null;
    }
    setIsPillarModalOpen(false);
    resetPillarModalState();
  }

  function openPillarCreateModal() {
    if (!selectedProductId || !hasProductContextPanel) {
      return;
    }
    closeCreateChooser();
    setPillarFormState(EMPTY_PILLAR_FORM);
    setIsPillarModalOpen(true);
    resetPillarModalState();
  }

  function resetMetricModalState() {
    setMetricFormError(null);
    setMetricSubmitting(false);
    setMetricModalStep("form");
  }

  function closeMetricCreateModal() {
    if (metricCloseTimeoutRef.current !== null) {
      window.clearTimeout(metricCloseTimeoutRef.current);
      metricCloseTimeoutRef.current = null;
    }
    setIsMetricModalOpen(false);
    resetMetricModalState();
  }

  function openMetricCreateModal() {
    if (!selectedPillarId || !isProductsPanel) {
      return;
    }
    closeCreateChooser();
    setMetricFormState(EMPTY_METRIC_FORM);
    setIsMetricModalOpen(true);
    resetMetricModalState();
  }

  function handleCreateChoice(target: CreateTarget) {
    if (target === "cliente") {
      openClientCreateModal();
      return;
    }
    if (target === "produto") {
      openProductCreateModal();
      return;
    }
    if (target === "mentor") {
      if (!hasProductContextPanel || !selectedProductId) {
        setCreateChooserMessage("Abra Produtos ou Mentores para selecionar um produto.");
        return;
      }
      openMentorCreateModal();
      return;
    }
    if (target === "pilar") {
      if (!hasProductContextPanel || !selectedProductId) {
        setCreateChooserMessage("Abra Produtos, Mentores ou Alunos para selecionar um produto.");
        return;
      }
      openPillarCreateModal();
      return;
    }
    if (target === "metrica") {
      if (!isProductsPanel || !selectedPillarId) {
        setCreateChooserMessage("Abra Produtos e selecione um pilar.");
        return;
      }
      openMetricCreateModal();
      return;
    }
    if (target === "aluno") {
      if (!(isMentorsPanel || isStudentsPanel) || !selectedMentorId) {
        setCreateChooserMessage("Abra Mentores ou Alunos para selecionar um mentor.");
        return;
      }
      openStudentCreateModal();
      return;
    }
    setCreateChooserMessage("Disponivel nos proximos blocos.");
  }

  function handlePrepareClientCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setClientFormError(null);
    setClientModalStep("confirm");
  }

  async function handleConfirmClientCreate() {
    setClientSubmitting(true);
    setClientFormError(null);
    try {
      const created = await createAdminClient({
        name: clientFormState.name.trim(),
        brand_name: clientFormState.brand_name.trim() || undefined,
        cnpj: clientFormState.cnpj.trim(),
        slug: clientFormState.slug.trim() || undefined,
        timezone: clientFormState.timezone.trim() || undefined,
        currency: clientFormState.currency.trim() || undefined,
        notes: clientFormState.notes.trim() || undefined
      });
      const items = await clientsResource.refresh();
      setSelectedClientId(created.id);
      if (!hasContextPanel && items.length > 0) {
        setSearchParams({});
      }
      setClientModalStep("success");
      clientCloseTimeoutRef.current = window.setTimeout(() => closeClientCreateModal(), 1200);
    } catch (error) {
      setClientFormError(toUserErrorMessage(error, "Falha ao cadastrar cliente."));
      setClientModalStep("form");
    } finally {
      setClientSubmitting(false);
    }
  }

  function handlePrepareProductCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProductFormError(null);
    setProductModalStep("confirm");
  }

  async function handleConfirmProductCreate() {
    if (!selectedClientId) {
      return;
    }
    setProductSubmitting(true);
    setProductFormError(null);
    try {
      const created = await createAdminProduct(selectedClientId, {
        name: productFormState.name.trim(),
        code: productFormState.code.trim(),
        slug: productFormState.slug.trim() || undefined,
        description: productFormState.description.trim() || undefined,
        delivery_model: productFormState.delivery_model.trim() || undefined
      });
      await productsResource.refresh();
      setSelectedProductId(created.id);
      setProductModalStep("success");
      productCloseTimeoutRef.current = window.setTimeout(() => closeProductCreateModal(), 1200);
    } catch (error) {
      setProductFormError(toUserErrorMessage(error, "Falha ao cadastrar produto."));
      setProductModalStep("form");
    } finally {
      setProductSubmitting(false);
    }
  }

  function handlePrepareMentorCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMentorFormError(null);
    setMentorModalStep("confirm");
  }

  async function handleConfirmMentorCreate() {
    if (!selectedProductId) {
      return;
    }
    setMentorSubmitting(true);
    setMentorFormError(null);
    try {
      await createAdminMentor(selectedProductId, {
        full_name: mentorFormState.full_name.trim(),
        cpf: mentorFormState.cpf.trim(),
        email: mentorFormState.email.trim(),
        phone: mentorFormState.phone.trim() || undefined,
        bio: mentorFormState.bio.trim() || undefined,
        notes: mentorFormState.notes.trim() || undefined
      });
      await Promise.all([mentorsResource.refresh(), productsResource.refresh()]);
      setMentorModalStep("success");
      mentorCloseTimeoutRef.current = window.setTimeout(() => closeMentorCreateModal(), 1200);
    } catch (error) {
      setMentorFormError(toUserErrorMessage(error, "Falha ao cadastrar mentor."));
      setMentorModalStep("form");
    } finally {
      setMentorSubmitting(false);
    }
  }

  function handlePrepareStudentCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStudentFormError(null);
    setStudentModalStep("confirm");
  }

  async function handleConfirmStudentCreate() {
    if (!selectedMentorId) {
      return;
    }
    setStudentSubmitting(true);
    setStudentFormError(null);
    try {
      await createAdminStudent(selectedMentorId, {
        full_name: studentFormState.full_name.trim(),
        cpf: studentFormState.cpf.trim(),
        email: studentFormState.email.trim() || undefined,
        phone: studentFormState.phone.trim() || undefined,
        notes: studentFormState.notes.trim() || undefined
      });
      await studentsResource.refresh();
      setStudentModalStep("success");
      studentCloseTimeoutRef.current = window.setTimeout(() => closeStudentCreateModal(), 1200);
    } catch (error) {
      setStudentFormError(toUserErrorMessage(error, "Falha ao cadastrar aluno."));
      setStudentModalStep("form");
    } finally {
      setStudentSubmitting(false);
    }
  }

  function handlePrepareStudentLinkAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStudentLinkError(null);
    setStudentLinkModalStep("confirm");
  }

  async function handleConfirmStudentLinkAction() {
    if (!selectedStudent) {
      return;
    }
    setStudentLinkSubmitting(true);
    setStudentLinkError(null);
    try {
      if (studentLinkMode === "reassign") {
        await reassignAdminStudent(selectedStudent.id, {
          target_mentor_id: studentLinkTargetMentorId,
          justificativa: studentLinkJustification.trim()
        });
      } else {
        await unlinkAdminStudent(selectedStudent.id, {
          justificativa: studentLinkJustification.trim()
        });
      }
      await studentsResource.refresh();
      setSelectedStudentId(null);
      setStudentLinkModalStep("success");
      studentLinkCloseTimeoutRef.current = window.setTimeout(() => closeStudentLinkModal(), 1200);
    } catch (error) {
      setStudentLinkError(toUserErrorMessage(error, "Falha ao atualizar vinculo do aluno."));
      setStudentLinkModalStep("form");
    } finally {
      setStudentLinkSubmitting(false);
    }
  }

  function handlePrepareIndicatorLoad(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIndicatorLoadError(null);

    if (indicatorMetricRows.length === 0) {
      setIndicatorLoadError("Nenhuma metrica ativa encontrada para o produto.");
      return;
    }

    const hasMissingMetricValues = indicatorMetricRows.some((row) => !row.baseline.trim() || !row.current.trim());
    if (hasMissingMetricValues) {
      setIndicatorLoadError("Preencha baseline e valor atual para todas as metricas ativas.");
      return;
    }

    if (!indicatorCheckpointForm.week.trim() || !indicatorCheckpointForm.label.trim()) {
      setIndicatorLoadError("Preencha ao menos um checkpoint inicial.");
      return;
    }

    setIndicatorLoadModalStep("confirm");
  }

  async function handleConfirmIndicatorLoad() {
    if (!selectedStudent) {
      return;
    }
    setIndicatorLoadSubmitting(true);
    setIndicatorLoadError(null);
    try {
      await loadAdminStudentIndicators(selectedStudent.id, {
        metric_values: indicatorMetricRows.map((row) => ({
          metric_id: row.metric_id,
          value_baseline: Number(row.baseline),
          value_current: Number(row.current),
          value_projected: row.projected.trim() ? Number(row.projected) : undefined,
          improving_trend: row.improving_trend
        })),
        checkpoints: [
          {
            week: Number(indicatorCheckpointForm.week),
            status: indicatorCheckpointForm.status,
            label: indicatorCheckpointForm.label.trim()
          }
        ]
      });
      setIndicatorLoadModalStep("success");
      indicatorLoadCloseTimeoutRef.current = window.setTimeout(() => closeIndicatorLoadModal(), 1200);
    } catch (error) {
      setIndicatorLoadError(toUserErrorMessage(error, "Falha ao carregar indicadores iniciais."));
      setIndicatorLoadModalStep("form");
    } finally {
      setIndicatorLoadSubmitting(false);
    }
  }

  function handlePreparePillarCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPillarFormError(null);
    setPillarModalStep("confirm");
  }

  async function handleConfirmPillarCreate() {
    if (!selectedProductId) {
      return;
    }
    setPillarSubmitting(true);
    setPillarFormError(null);
    try {
      const created = await createAdminPillar(selectedProductId, {
        name: pillarFormState.name.trim(),
        code: pillarFormState.code.trim() || undefined,
        order_index: Math.max(0, Number.parseInt(pillarFormState.order_index, 10) || 0)
      });
      await pillarsResource.refresh();
      setSelectedPillarId(created.id);
      setPillarModalStep("success");
      pillarCloseTimeoutRef.current = window.setTimeout(() => closePillarCreateModal(), 1200);
    } catch (error) {
      setPillarFormError(toUserErrorMessage(error, "Falha ao cadastrar pilar."));
      setPillarModalStep("form");
    } finally {
      setPillarSubmitting(false);
    }
  }

  function handlePrepareMetricCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMetricFormError(null);
    setMetricModalStep("confirm");
  }

  async function handleConfirmMetricCreate() {
    if (!selectedPillarId) {
      return;
    }
    setMetricSubmitting(true);
    setMetricFormError(null);
    try {
      await createAdminMetric(selectedPillarId, {
        name: metricFormState.name.trim(),
        code: metricFormState.code.trim() || undefined,
        direction: metricFormState.direction,
        unit: metricFormState.unit.trim() || undefined
      });
      await metricsResource.refresh();
      setMetricModalStep("success");
      metricCloseTimeoutRef.current = window.setTimeout(() => closeMetricCreateModal(), 1200);
    } catch (error) {
      setMetricFormError(toUserErrorMessage(error, "Falha ao cadastrar metrica."));
      setMetricModalStep("form");
    } finally {
      setMetricSubmitting(false);
    }
  }

  function openClientArea(clientId: string) {
    setSelectedClientId(clientId);
    setSearchParams({ panel: "clientes" });
  }

  function openProductArea(productId: string) {
    setSelectedProductId(productId);
    setSearchParams({ panel: "produtos" });
  }

  function openMentorArea(productId: string) {
    setSelectedProductId(productId);
    setSearchParams({ panel: "mentores" });
  }

  function openStudentArea(mentorId: string) {
    setSelectedMentorId(mentorId);
    setSearchParams({ panel: "alunos" });
  }

  function togglePillarStack() {
    if (pillarCards.length === 0) {
      return;
    }
    if (!isPillarExpanded && !selectedPillarId && pillarCards.length > 0) {
      setSelectedPillarId(pillarCards[0].id);
    }
    setIsPillarExpanded((current) => !current);
  }

  function toggleMetricStack(pillarId: string) {
    setSelectedPillarId((current) => (current === pillarId ? null : pillarId));
  }

  function renderCreateChooser() {
    return (
      <div className="admin-context-actions">
        <button type="button" className="admin-inline-cta" onClick={toggleCreateChooser}>
          Cadastrar...
        </button>
        {isCreateChooserOpen ? (
          <div className="admin-create-menu">
            <div className="admin-create-menu__grid">
              {CREATE_OPTIONS.map((option) => (
                <button key={option.key} type="button" className="admin-create-menu__item" onClick={() => handleCreateChoice(option.key)}>
                  {option.label}
                </button>
              ))}
            </div>
            {createChooserMessage ? <p className="admin-create-menu__message">{createChooserMessage}</p> : null}
          </div>
        ) : null}
      </div>
    );
  }




  async function loadApiCatalog() {
    setApiCatalogLoading(true);
    setApiCatalogError(null);
    try {
      const items = await listAdminApiOperations();
      setApiCatalog(items);
    } catch (error) {
      setApiCatalogError(toUserErrorMessage(error, "Falha ao carregar catalogo de requests."));
    } finally {
      setApiCatalogLoading(false);
    }
  }

  async function handleApiOperationRequest(item: AdminApiOperationItem) {
    const ok = window.confirm(`Confirmar request monitoravel para ${item.method} ${item.endpoint}?`);
    if (!ok) return;
    setApiExecutionStatusByEndpoint((current) => ({ ...current, [item.endpoint]: "Processando..." }));
    try {
      const response: AdminApiOperationExecution = await executeAdminApiOperation(item.endpoint);
      setApiExecutionStatusByEndpoint((current) => ({
        ...current,
        [item.endpoint]: `${response.status} | solicitado em ${response.requestedAt}`
      }));
    } catch (error) {
      setApiExecutionStatusByEndpoint((current) => ({
        ...current,
        [item.endpoint]: toUserErrorMessage(error, "Falha ao solicitar request.")
      }));
    }
  }

  async function loadDatabaseTables() {
    setDatabaseError(null);
    const tables = await listDatabaseTables();
    setDatabaseTables(tables);
  }

  async function loadDatabaseRecords(table: string, offset: number, append = false) {
    setDatabaseLoading(true);
    setDatabaseError(null);
    try {
      const page = await listDatabaseRecords(table, offset);
      setSelectedDatabaseTable(table);
      setDatabaseOffset(page.offset + page.items.length);
      setDatabaseTotal(page.total);
      setDatabaseRows((current) => (append ? [...current, ...page.items] : page.items));
    } catch (error) {
      setDatabaseError(toUserErrorMessage(error, "Falha ao carregar registros."));
    } finally {
      setDatabaseLoading(false);
    }
  }

  async function handleDatabaseRecordEdit(table: string, row: Record<string, unknown>) {
    const recordId = String(row.id ?? "");
    const field = window.prompt("Campo para editar:", "name");
    if (!field) return;
    const value = window.prompt("Novo valor:", String(row[field] ?? ""));
    if (value === null) return;
    const ok = window.confirm("Confirmar persistencia da alteracao?");
    if (!ok) return;
    try {
      const updated = await updateDatabaseRecord(table, recordId, { [field]: value });
      setDatabaseRows((current) => current.map((item) => (String(item.id ?? "") === recordId ? updated : item)));
      window.alert("Valor atualizado com sucesso.");
    } catch (error) {
      window.alert(toUserErrorMessage(error, "Falha ao atualizar valor."));
    }
  }

  function renderStudentPanelActions() {
    return (
      <div className="admin-panel-actions">
        {renderCreateChooser()}
        <button type="button" className="admin-inline-link admin-inline-link--button" onClick={() => void openIndicatorLoadModal()} disabled={!selectedStudent}>
          Carga inicial
        </button>
        <button type="button" className="admin-inline-link admin-inline-link--button" onClick={openStudentLinkModal} disabled={!selectedStudent}>
          Gerir vinculo
        </button>
      </div>
    );
  }

  function buildOperationalKey(mode: OperationalViewMode, rowId: string) {
    return `${mode}:${rowId}`;
  }

  function buildRadarOperationalKey(mode: OperationalViewMode, axisKey: string) {
    const studentKey = selectedStudentId ?? "sem-aluno";
    return `${mode}:${studentKey}:${axisKey}`;
  }

  function getCommandCenterDraft(mode: OperationalViewMode, studentId: string): EditableCommandCenterRow {
    const key = buildOperationalKey(mode, studentId);
    return commandCenterDrafts[key] ?? { progress: "0.0", engagement: "0.0", daysLeft: "45" };
  }

  function setCommandCenterDraftField(
    mode: OperationalViewMode,
    studentId: string,
    field: keyof EditableCommandCenterRow,
    value: string
  ) {
    const key = buildOperationalKey(mode, studentId);
    setCommandCenterDrafts((current) => ({
      ...current,
      [key]: {
        ...(current[key] ?? { progress: "0.0", engagement: "0.0", daysLeft: "45" }),
        [field]: value
      }
    }));
  }

  function getMatrixDraft(mode: OperationalViewMode, studentId: string): EditableMatrixRow {
    const key = buildOperationalKey(mode, studentId);
    return matrixDrafts[key] ?? {
      urgency: "watch",
      progress: "0.0",
      engagement: "0.0",
      daysLeft: "45",
      ltv: "0.00"
    };
  }

  function setMatrixDraftField(
    mode: OperationalViewMode,
    studentId: string,
    field: keyof EditableMatrixRow,
    value: string
  ) {
    const key = buildOperationalKey(mode, studentId);
    setMatrixDrafts((current) => ({
      ...current,
      [key]: {
        ...(current[key] ?? {
          urgency: "watch",
          progress: "0.0",
          engagement: "0.0",
          daysLeft: "45",
          ltv: "0.00"
        }),
        [field]: value as EditableMatrixRow[typeof field]
      }
    }));
  }

  function getRadarDraft(
    mode: OperationalViewMode,
    axis: { axisKey: string; baseline: number; current: number; projected: number }
  ): EditableRadarRow {
    const key = buildRadarOperationalKey(mode, axis.axisKey);
    return radarDrafts[key] ?? {
      baseline: toPercentInput(axis.baseline),
      current: toPercentInput(axis.current),
      projected: toPercentInput(axis.projected)
    };
  }

  function setRadarDraftField(
    mode: OperationalViewMode,
    axisKey: string,
    field: keyof EditableRadarRow,
    value: string
  ) {
    const key = buildRadarOperationalKey(mode, axisKey);
    setRadarDrafts((current) => ({
      ...current,
      [key]: {
        ...current[key],
        [field]: value
      }
    }));
  }

  function getProviderMetricDraft(metric: AdminMetricDto): EditableProviderMetricRow {
    return providerMetricDrafts[metric.id] ?? {
      name: metric.name,
      code: metric.code,
      unit: metric.unit ?? "",
      direction: metric.direction
    };
  }

  function setProviderMetricDraftField<Field extends keyof EditableProviderMetricRow>(
    metric: AdminMetricDto,
    field: Field,
    value: EditableProviderMetricRow[Field]
  ) {
    setProviderMetricDrafts((current) => ({
      ...current,
      [metric.id]: {
        ...(current[metric.id] ?? {
          name: metric.name,
          code: metric.code,
          unit: metric.unit ?? "",
          direction: metric.direction
        }),
        [field]: value
      }
    }));
  }

  useEffect(() => {
    if (!canLoadAdmin || !isDatabasePanel) return;
    void loadDatabaseTables();
  }, [canLoadAdmin, isDatabasePanel]);

  useEffect(() => {
    if (!canLoadAdmin || !isApiPanel) return;
    void loadApiCatalog();
  }, [canLoadAdmin, isApiPanel]);

  function renderOperationalView(mode: OperationalViewMode) {
    const isProviderMode = mode === "provider";
    const moduleLabel = isProviderMode ? "Provider View" : "Client View";
    const testId = isProviderMode ? "admin-provider-view-editable" : "admin-client-view-editable";
    const selectedMentorLabel = isProviderMode ? selectedProviderId : selectedMentorId;
    const providerCanSearch = Boolean(selectedClientId && selectedProductId && selectedProviderId);
    const providerHasSearch = Boolean(providerSearchMentorId);
    const studentsToRender = isProviderMode ? providerVisibleStudents : studentsResource.data;

    return (
      <article className="admin-module" aria-label={moduleLabel}>
        <p className="admin-module__eyebrow">{moduleLabel}</p>
        <div className="admin-provider-view-controls">
          <label className="admin-provider-view-control">
            <span>Cliente</span>
            <select value={isProviderMode ? (selectedClientId ?? "") : selectedClientViewClientId} onChange={(event) => {
              const value = event.target.value;
              if (isProviderMode) {
                setSelectedClientId(value || null);
              } else {
                setSelectedClientViewClientId(value);
              }
            }}>
              <option value="">Selecione</option>
              {activeClients.map((client) => (
                <option key={client.id} value={client.id}>{client.name}</option>
              ))}
            </select>
          </label>
          <label className="admin-provider-view-control">
            <span>Produto</span>
            <select value={selectedProductId ?? ""} onChange={(event) => setSelectedProductId(event.target.value || null)}>
              <option value="">Selecione</option>
              {productsResource.data.map((product) => (
                <option key={product.id} value={product.id}>{product.name}</option>
              ))}
            </select>
          </label>
          <label className="admin-provider-view-control">
            <span>Mentor</span>
            <select value={selectedMentorLabel ?? ""} onChange={(event) => {
              const value = event.target.value;
              if (isProviderMode) {
                setSelectedProviderId(value);
              } else {
                setSelectedMentorId(value || null);
              }
            }}>
              <option value="">Selecione</option>
              {mentorsResource.data.map((mentor) => (
                <option key={mentor.id} value={mentor.id}>{mentor.full_name}</option>
              ))}
            </select>
          </label>
          {!isProviderMode && (
            <label className="admin-provider-view-control">
              <span>Aluno</span>
              <select value={selectedStudentId ?? ""} onChange={(event) => setSelectedStudentId(event.target.value || null)}>
                <option value="">Selecione</option>
                {studentsResource.data.map((student) => (
                  <option key={student.id} value={student.id}>{student.full_name}</option>
                ))}
              </select>
            </label>
          )}
        </div>

        {isProviderMode && (
          <div className="admin-provider-view-actions">
            <button type="button" onClick={handleProviderSearchStudents} disabled={!providerCanSearch}>
              Buscar Alunos
            </button>
          </div>
        )}

        <p className="admin-module__muted" hidden={isProviderMode}>
          Edição tabular operacional para Centro de Comando, Matriz de Decisão e Radar.
        </p>

        {isProviderMode ? (
          <p className="admin-module__muted">Leitura operacional para distribuição da Matriz de Decisão e Radar por abas.</p>
        ) : null}

        {isProviderMode && !providerHasSearch ? (
          <p className="admin-state">Selecione Cliente, Produto e Mentor e clique em Buscar Alunos.</p>
        ) : null}
        {studentsResource.loading && studentsResource.data.length === 0 && (!isProviderMode || providerHasSearch) ? (
          <p className="admin-state">Carregando alunos do contexto...</p>
        ) : null}
        {studentsResource.error && studentsResource.data.length === 0 && (!isProviderMode || providerHasSearch) ? (
          <p className="admin-form-error">{studentsResource.error}</p>
        ) : null}
        {!studentsResource.loading && !studentsResource.error && studentsResource.data.length === 0 && (!isProviderMode || providerHasSearch) ? (
          <p className="admin-state">Sem alunos vinculados para o contexto selecionado.</p>
        ) : null}

        {studentsToRender.length > 0 ? (
          <div className="admin-provider-view-edit-grid" data-testid={testId}>
            {!isProviderMode ? (
            <section>
              <h3>Centro de Comando</h3>
              <div className="admin-data-table-wrapper">
                <table className="admin-data-table" aria-label={`${moduleLabel} - Centro de Comando`}>
                  <thead>
                    <tr>
                      <th scope="col">Aluno</th>
                      <th scope="col">Progresso (%)</th>
                      <th scope="col">Engajamento (%)</th>
                      <th scope="col">Dias (D)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentsToRender.map((student) => {
                      const draft = getCommandCenterDraft(mode, student.id);
                      return (
                        <tr key={`cc-${student.id}`}>
                          <td>{student.full_name}</td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Centro Progresso ${student.full_name}`}
                              type="number"
                              step="0.1"
                              value={draft.progress}
                              onChange={(event) => setCommandCenterDraftField(mode, student.id, "progress", event.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Centro Engajamento ${student.full_name}`}
                              type="number"
                              step="0.1"
                              value={draft.engagement}
                              onChange={(event) => setCommandCenterDraftField(mode, student.id, "engagement", event.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Centro Dias ${student.full_name}`}
                              type="number"
                              step="1"
                              min="0"
                              value={draft.daysLeft}
                              onChange={(event) => setCommandCenterDraftField(mode, student.id, "daysLeft", event.target.value)}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
            ) : null}

            {isProviderMode ? (
            <section>
              <h3>Matriz de Decisão</h3>
              <p className="admin-module__muted">Distribuição dos alunos por quadrante no contexto selecionado.</p>
              <div className="admin-matrix-distribution" aria-label={`${moduleLabel} - Distribuição por quadrante`}>
                {URGENCY_OPTIONS.map((option) => {
                  const count = studentsResource.data.filter((student) => getMatrixDraft(mode, student.id).urgency === option.value).length;
                  const percentage = studentsResource.data.length === 0 ? 0 : (count / studentsResource.data.length) * 100;
                  return (
                    <article key={option.value} className="admin-matrix-distribution-card">
                      <span>{option.label}</span>
                      <strong>{count}</strong>
                      <small>{percentage.toFixed(1)}% dos alunos</small>
                      <div className="admin-matrix-distribution-card__bar" aria-hidden="true">
                        <span style={{ width: `${percentage}%` }} />
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
            ) : (
            <section>
              <h3>Matriz de Decisão</h3>
              <div className="admin-data-table-wrapper">
                <table className="admin-data-table" aria-label={`${moduleLabel} - Matriz de Decisão`}>
                  <thead>
                    <tr>
                      <th scope="col">Aluno</th>
                      <th scope="col">Urgência</th>
                      <th scope="col">Progresso (%)</th>
                      <th scope="col">Engajamento (%)</th>
                      <th scope="col">Dias (D)</th>
                      <th scope="col">LTV (R$)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {studentsToRender.map((student) => {
                      const draft = getMatrixDraft(mode, student.id);
                      return (
                        <tr key={`mx-${student.id}`}>
                          <td>{student.full_name}</td>
                          <td>
                            <select
                              aria-label={`${moduleLabel} Matriz Urgência ${student.full_name}`}
                              value={draft.urgency}
                              onChange={(event) => setMatrixDraftField(mode, student.id, "urgency", event.target.value)}
                            >
                              {URGENCY_OPTIONS.map((option) => (
                                <option key={option.value} value={option.value}>{option.label}</option>
                              ))}
                            </select>
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Matriz Progresso ${student.full_name}`}
                              type="number"
                              step="0.1"
                              value={draft.progress}
                              onChange={(event) => setMatrixDraftField(mode, student.id, "progress", event.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Matriz Engajamento ${student.full_name}`}
                              type="number"
                              step="0.1"
                              value={draft.engagement}
                              onChange={(event) => setMatrixDraftField(mode, student.id, "engagement", event.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Matriz Dias ${student.full_name}`}
                              type="number"
                              step="1"
                              min="0"
                              value={draft.daysLeft}
                              onChange={(event) => setMatrixDraftField(mode, student.id, "daysLeft", event.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              aria-label={`${moduleLabel} Matriz LTV ${student.full_name}`}
                              type="number"
                              step="0.01"
                              min="0"
                              value={draft.ltv}
                              onChange={(event) => setMatrixDraftField(mode, student.id, "ltv", event.target.value)}
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
            )}

            <section>
              <h3>Radar</h3>
              {isProviderMode ? (
                <>
                  <div className="admin-radar-controls">
                    <label className="admin-provider-view-control">
                      <span>Aluno do Radar</span>
                      <select value={selectedStudentId ?? ""} onChange={(event) => setSelectedStudentId(event.target.value || null)}>
                        <option value="">Selecione</option>
                        {studentsResource.data.map((student) => (
                          <option key={student.id} value={student.id}>{student.full_name}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="admin-radar-tabs" role="tablist" aria-label="Abas do Radar Provider">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={providerRadarTab === "pillars"}
                      className={providerRadarTab === "pillars" ? "is-active" : ""}
                      onClick={() => setProviderRadarTab("pillars")}
                    >
                      Pilares
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={providerRadarTab === "metrics"}
                      className={providerRadarTab === "metrics" ? "is-active" : ""}
                      onClick={() => setProviderRadarTab("metrics")}
                    >
                      Métricas
                    </button>
                  </div>
                  {!selectedStudentId ? (
                    <p className="admin-state">Selecione um aluno para visualizar o radar.</p>
                  ) : clientViewRadarResource.loading ? (
                    <p className="admin-state">Carregando radar...</p>
                  ) : clientViewRadarResource.error ? (
                    <p className="admin-state">{clientViewRadarResource.error}</p>
                  ) : clientViewRadarResource.data.axisScores.length === 0 ? (
                    <p className="admin-state">Sem dados de radar para leitura neste contexto.</p>
                  ) : providerRadarTab === "pillars" ? (
                    <div className="admin-data-table-wrapper">
                      <table className="admin-data-table" aria-label={`${moduleLabel} - Radar Pilares`}>
                        <thead>
                          <tr>
                            <th scope="col">Pilar</th>
                            <th scope="col">Baseline (%)</th>
                            <th scope="col">Atual (%)</th>
                            <th scope="col">Projetado (%)</th>
                            <th scope="col">Leitura</th>
                          </tr>
                        </thead>
                        <tbody>
                          {clientViewRadarResource.data.axisScores.map((axis) => (
                            <tr key={`rd-provider-pillar-${axis.axisKey}`}>
                              <td>{axis.axisLabel}</td>
                              <td><span className="admin-readonly-value">{toPercentInput(axis.baseline)}</span></td>
                              <td><span className="admin-readonly-value">{toPercentInput(axis.current)}</span></td>
                              <td><span className="admin-readonly-value">{toPercentInput(axis.projected)}</span></td>
                              <td>{axis.insight ?? "-"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <>
                      <div className="admin-radar-controls">
                        <label className="admin-provider-view-control">
                          <span>Pilar</span>
                          <select value={selectedPillarId ?? ""} onChange={(event) => setSelectedPillarId(event.target.value || null)}>
                            {clientViewRadarResource.data.axisScores.map((axis) => (
                              <option key={axis.axisKey} value={axis.axisId ?? ""}>{axis.axisLabel}</option>
                            ))}
                          </select>
                        </label>
                      </div>
                      {metricsResource.loading ? (
                        <p className="admin-state">Carregando métricas...</p>
                      ) : metricsResource.error ? (
                        <p className="admin-state">{metricsResource.error}</p>
                      ) : metricsResource.data.length === 0 ? (
                        <p className="admin-state">Sem métricas cadastradas para o pilar selecionado.</p>
                      ) : (
                        <div className="admin-data-table-wrapper">
                          <table className="admin-data-table" aria-label={`${moduleLabel} - Radar Métricas`}>
                            <thead>
                              <tr>
                                <th scope="col">Métrica</th>
                                <th scope="col">Código</th>
                                <th scope="col">Unidade</th>
                                <th scope="col">Direção</th>
                              </tr>
                            </thead>
                            <tbody>
                              {metricsResource.data.map((metric) => {
                                const draft = getProviderMetricDraft(metric);
                                return (
                                  <tr key={`rd-provider-metric-${metric.id}`}>
                                    <td>
                                      <input
                                        aria-label={`${moduleLabel} Radar Métrica Nome ${metric.name}`}
                                        value={draft.name}
                                        onChange={(event) => setProviderMetricDraftField(metric, "name", event.target.value)}
                                      />
                                    </td>
                                    <td>
                                      <input
                                        aria-label={`${moduleLabel} Radar Métrica Código ${metric.name}`}
                                        value={draft.code}
                                        onChange={(event) => setProviderMetricDraftField(metric, "code", event.target.value)}
                                      />
                                    </td>
                                    <td>
                                      <input
                                        aria-label={`${moduleLabel} Radar Métrica Unidade ${metric.name}`}
                                        value={draft.unit}
                                        onChange={(event) => setProviderMetricDraftField(metric, "unit", event.target.value)}
                                      />
                                    </td>
                                    <td>
                                      <select
                                        aria-label={`${moduleLabel} Radar Métrica Direção ${metric.name}`}
                                        value={draft.direction}
                                        onChange={(event) => setProviderMetricDraftField(metric, "direction", event.target.value as AdminMetricDirection)}
                                      >
                                        {METRIC_DIRECTION_OPTIONS.map((option) => (
                                          <option key={option.value} value={option.value}>{option.label}</option>
                                        ))}
                                      </select>
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </>
                  )}
                </>
              ) : (
                <>
              {!selectedStudentId ? (
                <p className="admin-state">Selecione um aluno para editar os eixos do radar.</p>
              ) : clientViewRadarResource.loading ? (
                <p className="admin-state">Carregando radar...</p>
              ) : clientViewRadarResource.error ? (
                <p className="admin-state">{clientViewRadarResource.error}</p>
              ) : clientViewRadarResource.data.axisScores.length === 0 ? (
                <p className="admin-state">Sem dados de radar para leitura neste contexto.</p>
              ) : (
                <div className="admin-data-table-wrapper">
                  <table className="admin-data-table" aria-label={`${moduleLabel} - Radar`}>
                    <thead>
                      <tr>
                        <th scope="col">Eixo</th>
                        <th scope="col">Baseline (%)</th>
                        <th scope="col">Atual (%)</th>
                        <th scope="col">Projetado (%)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {clientViewRadarResource.data.axisScores.map((axis) => {
                        const draft = getRadarDraft(mode, axis);
                        return (
                          <tr key={`rd-${axis.axisKey}`}>
                            <td>{axis.axisLabel}</td>
                            <td>
                              <input
                                aria-label={`${moduleLabel} Radar Baseline ${axis.axisLabel}`}
                                type="number"
                                step="0.1"
                                value={draft.baseline}
                                onChange={(event) => setRadarDraftField(mode, axis.axisKey, "baseline", event.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                aria-label={`${moduleLabel} Radar Atual ${axis.axisLabel}`}
                                type="number"
                                step="0.1"
                                value={draft.current}
                                onChange={(event) => setRadarDraftField(mode, axis.axisKey, "current", event.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                aria-label={`${moduleLabel} Radar Projetado ${axis.axisLabel}`}
                                type="number"
                                step="0.1"
                                value={draft.projected}
                                onChange={(event) => setRadarDraftField(mode, axis.axisKey, "projected", event.target.value)}
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
                </>
              )}
            </section>
            {isProviderMode && studentsResource.data.length > providerStudentsPageSize ? (
              <div className="admin-pagination" aria-label="Paginação de alunos da Provider View">
                <button type="button" onClick={() => setProviderStudentsPage((current) => Math.max(1, current - 1))} disabled={providerStudentsPage === 1}>
                  Anterior
                </button>
                <span>
                  Página {providerStudentsPage} de {providerStudentsTotalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setProviderStudentsPage((current) => Math.min(providerStudentsTotalPages, current + 1))}
                  disabled={providerStudentsPage === providerStudentsTotalPages}
                >
                  Próxima
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </article>
    );
  }


  return (
    <AdminShell
      title="Admin"
      description="Views operacionais de apoio para Provider, Client, Database e API."
    >
      <section className="admin-page">

        {isProviderPanel ? renderOperationalView("provider") : null}
        {isClientViewPanel ? renderOperationalView("client") : null}
        {!isAuthenticated || user?.role !== "admin" ? (
          <section className="admin-notice">
            <strong>Entre com o usuario admin para operar o bloco real.</strong>
            <p>Use credenciais administrativas validas para este ambiente. Sem essa sessao, a API administrativa respondera com erro de autorizacao.</p>
          </section>
        ) : null}


        {isApiPanel ? (
          <section className="admin-module">
            <p className="admin-module__eyebrow">API</p>
            <h2>Catalogo didatico de requests monitoraveis</h2>
            <p className="admin-module__muted">Operacoes controladas com confirmacao explicita e trilha critica de auditoria.</p>
            {apiCatalogLoading ? <p className="admin-state">Carregando catalogo...</p> : null}
            {apiCatalogError ? <p className="admin-form-error">{apiCatalogError}</p> : null}
            {!apiCatalogLoading && !apiCatalogError ? (
              <ul className="admin-student-list" aria-label="Catalogo API">
                {apiCatalog.map((item) => (
                  <li key={item.endpoint} className="admin-student-card">
                    <h3>{item.name}</h3>
                    <p>{item.description}</p>
                    <p><strong>{item.method}</strong> {item.endpoint}</p>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleApiOperationRequest(item)}>Solicitar request</button>
                    {apiExecutionStatusByEndpoint[item.endpoint] ? <p className="admin-module__muted">{apiExecutionStatusByEndpoint[item.endpoint]}</p> : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {isDatabasePanel ? (
          <section className="admin-module">
            <p className="admin-module__eyebrow">Database View</p>
            <h2>Tabelas permitidas</h2>
            <ul className="admin-client-grid">
              {databaseTables.map((table) => (
                <li key={table}>
                  <button type="button" className="admin-client-card" onClick={() => void loadDatabaseRecords(table, 0)}>{table} <small>Ver Valores</small></button>
                </li>
              ))}
            </ul>
            {databaseError ? <p className="admin-form-error">{databaseError}</p> : null}
            {selectedDatabaseTable ? <h3>{selectedDatabaseTable}</h3> : null}
            {selectedDatabaseTable && !databaseLoading && databaseRows.length === 0 ? <p className="admin-state">Sem registros para esta tabela.</p> : null}
            {databaseRows.length > 0 ? (
              <div className="admin-data-table-wrapper">
                <table className="admin-data-table" aria-label={`Registros de ${selectedDatabaseTable}`}>
                  <thead>
                    <tr>
                      {databaseColumns.map((column) => (
                        <th key={column} scope="col">{column}</th>
                      ))}
                      <th scope="col">Acoes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {databaseRows.map((row, index) => (
                      <tr key={`${String(row.id ?? index)}`}>
                        {databaseColumns.map((column) => (
                          <td key={`${String(row.id ?? index)}-${column}`}>{formatDatabaseCell(row[column])}</td>
                        ))}
                        <td>
                          <button type="button" className="admin-inline-link admin-inline-link--button" onClick={() => void handleDatabaseRecordEdit(selectedDatabaseTable, row)}>
                            Editar valor
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {selectedDatabaseTable && databaseOffset < databaseTotal ? <button type="button" className="admin-inline-cta" onClick={() => void loadDatabaseRecords(selectedDatabaseTable, databaseOffset, true)} disabled={databaseLoading}>{databaseLoading ? "Carregando..." : "Carregar +10"}</button> : null}
          </section>
        ) : null}

        {isClientModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-client-modal-title">
              {clientModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Cliente/Empresa</p>
                      <h2 id="admin-client-modal-title">Cadastrar cliente</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeClientCreateModal}>
                      Fechar
                    </button>
                  </div>

                  <form className="admin-client-form" onSubmit={handlePrepareClientCreate}>
                    <label>
                      <span>Nome empresarial</span>
                      <input name="name" value={clientFormState.name} onChange={(event) => setClientFormState((current) => ({ ...current, name: event.target.value }))} required />
                    </label>
                    <label>
                      <span>Nome fantasia</span>
                      <input name="brand_name" value={clientFormState.brand_name} onChange={(event) => setClientFormState((current) => ({ ...current, brand_name: event.target.value }))} />
                    </label>
                    <label>
                      <span>CNPJ</span>
                      <input
                        name="cnpj"
                        value={clientFormState.cnpj}
                        onChange={(event) => setClientFormState((current) => ({ ...current, cnpj: formatCnpj(event.target.value) }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Slug</span>
                      <input name="slug" value={clientFormState.slug} onChange={(event) => setClientFormState((current) => ({ ...current, slug: event.target.value }))} />
                    </label>
                    <label>
                      <span>Timezone</span>
                      <input
                        name="timezone"
                        value={clientFormState.timezone}
                        onChange={(event) => setClientFormState((current) => ({ ...current, timezone: event.target.value }))}
                      />
                    </label>
                    <label>
                      <span>Moeda</span>
                      <input
                        name="currency"
                        value={clientFormState.currency}
                        onChange={(event) => setClientFormState((current) => ({ ...current, currency: event.target.value }))}
                      />
                    </label>
                    <label className="admin-client-form__full">
                      <span>Observacoes</span>
                      <textarea name="notes" rows={4} value={clientFormState.notes} onChange={(event) => setClientFormState((current) => ({ ...current, notes: event.target.value }))} />
                    </label>
                    {clientFormError ? <p className="admin-form-error">{clientFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeClientCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {clientModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Cliente/Empresa</p>
                      <h2 id="admin-client-modal-title">Confirmar cadastro do cliente</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{clientFormState.name}</strong>
                    </p>
                    <p>{formatCnpj(clientFormState.cnpj)}</p>
                  </div>
                  {clientFormError ? <p className="admin-form-error">{clientFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setClientModalStep("form")} disabled={clientSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmClientCreate()} disabled={clientSubmitting}>
                      {clientSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {clientModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-client-modal-title">Cliente cadastrado</h2>
                  <p>O cadastro foi concluido com sucesso. A tela sera atualizada automaticamente.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isProductModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-product-modal-title">
              {productModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Produto/Mentoria</p>
                      <h2 id="admin-product-modal-title">Cadastrar produto</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeProductCreateModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareProductCreate}>
                    <label>
                      <span>Nome do produto</span>
                      <input name="name" value={productFormState.name} onChange={(event) => setProductFormState((current) => ({ ...current, name: event.target.value }))} required />
                    </label>
                    <label>
                      <span>Codigo</span>
                      <input name="code" value={productFormState.code} onChange={(event) => setProductFormState((current) => ({ ...current, code: event.target.value }))} required />
                    </label>
                    <label>
                      <span>Slug</span>
                      <input name="slug" value={productFormState.slug} onChange={(event) => setProductFormState((current) => ({ ...current, slug: event.target.value }))} />
                    </label>
                    <label>
                      <span>Entrega</span>
                      <input
                        name="delivery_model"
                        value={productFormState.delivery_model}
                        onChange={(event) => setProductFormState((current) => ({ ...current, delivery_model: event.target.value }))}
                      />
                    </label>
                    <label className="admin-client-form__full">
                      <span>Descricao</span>
                      <textarea
                        name="description"
                        rows={4}
                        value={productFormState.description}
                        onChange={(event) => setProductFormState((current) => ({ ...current, description: event.target.value }))}
                      />
                    </label>
                    {productFormError ? <p className="admin-form-error">{productFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeProductCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {productModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Produto/Mentoria</p>
                      <h2 id="admin-product-modal-title">Confirmar cadastro do produto</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{productFormState.name}</strong>
                    </p>
                    <p>{productFormState.code}</p>
                  </div>
                  {productFormError ? <p className="admin-form-error">{productFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setProductModalStep("form")} disabled={productSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmProductCreate()} disabled={productSubmitting}>
                      {productSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {productModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-product-modal-title">Produto cadastrado</h2>
                  <p>O produto foi vinculado ao cliente e ja aparece na area administrativa.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isMentorModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-mentor-modal-title">
              {mentorModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Mentor</p>
                      <h2 id="admin-mentor-modal-title">Cadastrar mentor</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeMentorCreateModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareMentorCreate}>
                    <label>
                      <span>Nome completo</span>
                      <input
                        name="full_name"
                        value={mentorFormState.full_name}
                        onChange={(event) => setMentorFormState((current) => ({ ...current, full_name: event.target.value }))}
                        required
                      />
                    </label>
                    <label>
                      <span>CPF</span>
                      <input
                        name="cpf"
                        value={mentorFormState.cpf}
                        onChange={(event) => setMentorFormState((current) => ({ ...current, cpf: formatCpf(event.target.value) }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Email</span>
                      <input
                        name="email"
                        type="email"
                        value={mentorFormState.email}
                        onChange={(event) => setMentorFormState((current) => ({ ...current, email: event.target.value }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Telefone</span>
                      <input name="phone" value={mentorFormState.phone} onChange={(event) => setMentorFormState((current) => ({ ...current, phone: event.target.value }))} />
                    </label>
                    <label className="admin-client-form__full">
                      <span>Bio</span>
                      <textarea name="bio" rows={3} value={mentorFormState.bio} onChange={(event) => setMentorFormState((current) => ({ ...current, bio: event.target.value }))} />
                    </label>
                    <label className="admin-client-form__full">
                      <span>Observacoes</span>
                      <textarea name="notes" rows={3} value={mentorFormState.notes} onChange={(event) => setMentorFormState((current) => ({ ...current, notes: event.target.value }))} />
                    </label>
                    {mentorFormError ? <p className="admin-form-error">{mentorFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeMentorCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {mentorModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Mentor</p>
                      <h2 id="admin-mentor-modal-title">Confirmar cadastro do mentor</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{mentorFormState.full_name}</strong>
                    </p>
                    <p>{mentorFormState.email}</p>
                    <p>{formatCpf(mentorFormState.cpf)}</p>
                  </div>
                  {mentorFormError ? <p className="admin-form-error">{mentorFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setMentorModalStep("form")} disabled={mentorSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmMentorCreate()} disabled={mentorSubmitting}>
                      {mentorSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {mentorModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-mentor-modal-title">Mentor cadastrado</h2>
                  <p>O mentor foi vinculado ao produto e ja aparece no fluxo administrativo.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isStudentModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-student-modal-title">
              {studentModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Aluno</p>
                      <h2 id="admin-student-modal-title">Cadastrar aluno</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeStudentCreateModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareStudentCreate}>
                    <label>
                      <span>Nome completo</span>
                      <input
                        name="full_name"
                        value={studentFormState.full_name}
                        onChange={(event) => setStudentFormState((current) => ({ ...current, full_name: event.target.value }))}
                        required
                      />
                    </label>
                    <label>
                      <span>CPF</span>
                      <input
                        name="cpf"
                        value={studentFormState.cpf}
                        onChange={(event) => setStudentFormState((current) => ({ ...current, cpf: formatCpf(event.target.value) }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Email</span>
                      <input
                        name="email"
                        type="email"
                        value={studentFormState.email}
                        onChange={(event) => setStudentFormState((current) => ({ ...current, email: event.target.value }))}
                      />
                    </label>
                    <label>
                      <span>Telefone</span>
                      <input name="phone" value={studentFormState.phone} onChange={(event) => setStudentFormState((current) => ({ ...current, phone: event.target.value }))} />
                    </label>
                    <label className="admin-client-form__full">
                      <span>Observacoes</span>
                      <textarea name="notes" rows={3} value={studentFormState.notes} onChange={(event) => setStudentFormState((current) => ({ ...current, notes: event.target.value }))} />
                    </label>
                    {studentFormError ? <p className="admin-form-error">{studentFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeStudentCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {studentModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Aluno</p>
                      <h2 id="admin-student-modal-title">Confirmar cadastro do aluno</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{studentFormState.full_name}</strong>
                    </p>
                    <p>{formatCpf(studentFormState.cpf)}</p>
                    {studentFormState.email ? <p>{studentFormState.email}</p> : null}
                  </div>
                  {studentFormError ? <p className="admin-form-error">{studentFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setStudentModalStep("form")} disabled={studentSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmStudentCreate()} disabled={studentSubmitting}>
                      {studentSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {studentModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-student-modal-title">Aluno cadastrado</h2>
                  <p>O aluno foi vinculado ao mentor e ja aparece na area administrativa.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isStudentLinkModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-student-link-modal-title">
              {studentLinkModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Vinculo do aluno</p>
                      <h2 id="admin-student-link-modal-title">Gerir vinculo do aluno</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeStudentLinkModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareStudentLinkAction}>
                    <label className="admin-client-form__full">
                      <span>Aluno</span>
                      <input value={selectedStudent?.full_name || ""} readOnly />
                    </label>
                    <label>
                      <span>Acao</span>
                      <select
                        value={studentLinkMode}
                        onChange={(event) => setStudentLinkMode(event.target.value as StudentLinkMode)}
                      >
                        <option value="reassign" disabled={availableMentorsForRelink.length === 0}>
                          Reatribuir mentor
                        </option>
                        <option value="unlink">Desvincular aluno</option>
                      </select>
                    </label>
                    {studentLinkMode === "reassign" ? (
                      <label>
                        <span>Novo mentor</span>
                        <select
                          value={studentLinkTargetMentorId}
                          onChange={(event) => setStudentLinkTargetMentorId(event.target.value)}
                          required
                        >
                          {availableMentorsForRelink.map((mentor) => (
                            <option key={mentor.id} value={mentor.id}>
                              {mentor.full_name}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    <label className="admin-client-form__full">
                      <span>Justificativa</span>
                      <textarea
                        rows={4}
                        value={studentLinkJustification}
                        onChange={(event) => setStudentLinkJustification(event.target.value)}
                        required
                      />
                    </label>
                    {studentLinkError ? <p className="admin-form-error">{studentLinkError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeStudentLinkModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta" disabled={studentLinkMode === "reassign" && availableMentorsForRelink.length === 0}>
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {studentLinkModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Vinculo do aluno</p>
                      <h2 id="admin-student-link-modal-title">
                        {studentLinkMode === "reassign" ? "Confirmar reatribuicao" : "Confirmar desvinculo"}
                      </h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{selectedStudent?.full_name}</strong>
                    </p>
                    {studentLinkMode === "reassign"
                      ? <p>{mentorsResource.data.find((mentor) => mentor.id === studentLinkTargetMentorId)?.full_name || "Novo mentor"}</p>
                      : <p>Desvinculo logico do mentor atual</p>}
                    <p>{studentLinkJustification}</p>
                  </div>
                  {studentLinkError ? <p className="admin-form-error">{studentLinkError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setStudentLinkModalStep("form")} disabled={studentLinkSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmStudentLinkAction()} disabled={studentLinkSubmitting}>
                      {studentLinkSubmitting ? "Processando..." : "Confirmar"}
                    </button>
                  </div>
                </>
              ) : null}

              {studentLinkModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-student-link-modal-title">Vinculo atualizado</h2>
                  <p>O historico foi preservado e a carteira do mentor foi atualizada.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isIndicatorLoadModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-indicator-load-modal-title">
              {indicatorLoadModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Carga inicial</p>
                      <h2 id="admin-indicator-load-modal-title">Carregar indicadores iniciais</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeIndicatorLoadModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareIndicatorLoad}>
                    <label className="admin-client-form__full">
                      <span>Aluno</span>
                      <input value={selectedStudent?.full_name || ""} readOnly />
                    </label>

                    {indicatorCatalogLoading ? <p className="admin-state">Carregando metricas do produto...</p> : null}
                    {indicatorCatalogError ? <p className="admin-form-error">{indicatorCatalogError}</p> : null}

                    {!indicatorCatalogLoading && !indicatorCatalogError ? (
                      <div className="admin-indicator-grid admin-client-form__full">
                        {indicatorMetricRows.map((row, index) => (
                          <article key={row.metric_id} className="admin-indicator-card">
                            <strong>{row.name}</strong>
                            <small>{row.pillar_name ? `${row.pillar_name} | ${row.unit}` : row.unit}</small>
                            <label>
                              <span>{`Baseline - ${row.name}`}</span>
                              <input
                                type="number"
                                step="0.01"
                                value={row.baseline}
                                onChange={(event) =>
                                  setIndicatorMetricRows((current) =>
                                    current.map((item, itemIndex) => (itemIndex === index ? { ...item, baseline: event.target.value } : item))
                                  )
                                }
                                required
                              />
                            </label>
                            <label>
                              <span>{`Atual - ${row.name}`}</span>
                              <input
                                type="number"
                                step="0.01"
                                value={row.current}
                                onChange={(event) =>
                                  setIndicatorMetricRows((current) =>
                                    current.map((item, itemIndex) => (itemIndex === index ? { ...item, current: event.target.value } : item))
                                  )
                                }
                                required
                              />
                            </label>
                            <label>
                              <span>{`Projetado - ${row.name}`}</span>
                              <input
                                type="number"
                                step="0.01"
                                value={row.projected}
                                onChange={(event) =>
                                  setIndicatorMetricRows((current) =>
                                    current.map((item, itemIndex) => (itemIndex === index ? { ...item, projected: event.target.value } : item))
                                  )
                                }
                              />
                            </label>
                            <label className="admin-indicator-check">
                              <input
                                type="checkbox"
                                checked={row.improving_trend}
                                onChange={(event) =>
                                  setIndicatorMetricRows((current) =>
                                    current.map((item, itemIndex) => (itemIndex === index ? { ...item, improving_trend: event.target.checked } : item))
                                  )
                                }
                              />
                              <span>{`Tendencia positiva - ${row.name}`}</span>
                            </label>
                          </article>
                        ))}
                      </div>
                    ) : null}

                    <div className="admin-checkpoint-grid admin-client-form__full">
                      <label>
                        <span>Semana inicial</span>
                        <input
                          type="number"
                          min="0"
                          value={indicatorCheckpointForm.week}
                          onChange={(event) => setIndicatorCheckpointForm((current) => ({ ...current, week: event.target.value }))}
                          required
                        />
                      </label>
                      <label>
                        <span>Status do checkpoint</span>
                        <select
                          value={indicatorCheckpointForm.status}
                          onChange={(event) =>
                            setIndicatorCheckpointForm((current) => ({
                              ...current,
                              status: event.target.value as typeof current.status
                            }))
                          }
                        >
                          <option value="green">Green</option>
                          <option value="yellow">Yellow</option>
                          <option value="red">Red</option>
                        </select>
                      </label>
                      <label className="admin-client-form__full">
                        <span>Label do checkpoint</span>
                        <input
                          value={indicatorCheckpointForm.label}
                          onChange={(event) => setIndicatorCheckpointForm((current) => ({ ...current, label: event.target.value }))}
                          required
                        />
                      </label>
                    </div>

                    {indicatorLoadError ? <p className="admin-form-error">{indicatorLoadError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeIndicatorLoadModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta" disabled={indicatorCatalogLoading || indicatorMetricRows.length === 0}>
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {indicatorLoadModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Carga inicial</p>
                      <h2 id="admin-indicator-load-modal-title">Confirmar carga inicial</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{selectedStudent?.full_name}</strong>
                    </p>
                    <p>{`${indicatorMetricRows.length} metricas preparadas`}</p>
                    <p>{`Checkpoint: semana ${indicatorCheckpointForm.week} / ${indicatorCheckpointForm.status}`}</p>
                  </div>
                  {indicatorLoadError ? <p className="admin-form-error">{indicatorLoadError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setIndicatorLoadModalStep("form")} disabled={indicatorLoadSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmIndicatorLoad()} disabled={indicatorLoadSubmitting}>
                      {indicatorLoadSubmitting ? "Processando..." : "Confirmar carga"}
                    </button>
                  </div>
                </>
              ) : null}

              {indicatorLoadModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-indicator-load-modal-title">Carga inicial concluida</h2>
                  <p>O aluno agora possui indicadores iniciais prontos para Centro, Radar e Matriz.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isPillarModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-pillar-modal-title">
              {pillarModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Pilar</p>
                      <h2 id="admin-pillar-modal-title">Cadastrar pilar</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closePillarCreateModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePreparePillarCreate}>
                    <label>
                      <span>Nome do pilar</span>
                      <input
                        name="name"
                        value={pillarFormState.name}
                        onChange={(event) => setPillarFormState((current) => ({ ...current, name: event.target.value }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Codigo</span>
                      <input
                        name="code"
                        value={pillarFormState.code}
                        onChange={(event) => setPillarFormState((current) => ({ ...current, code: event.target.value }))}
                      />
                    </label>
                    <label>
                      <span>Ordem</span>
                      <input
                        name="order_index"
                        type="number"
                        min="0"
                        value={pillarFormState.order_index}
                        onChange={(event) => setPillarFormState((current) => ({ ...current, order_index: event.target.value }))}
                      />
                    </label>
                    {pillarFormError ? <p className="admin-form-error">{pillarFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closePillarCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {pillarModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Pilar</p>
                      <h2 id="admin-pillar-modal-title">Confirmar cadastro do pilar</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{pillarFormState.name}</strong>
                    </p>
                    {pillarFormState.code ? <p>{pillarFormState.code}</p> : null}
                    <p>Ordem {pillarFormState.order_index}</p>
                  </div>
                  {pillarFormError ? <p className="admin-form-error">{pillarFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setPillarModalStep("form")} disabled={pillarSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmPillarCreate()} disabled={pillarSubmitting}>
                      {pillarSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {pillarModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-pillar-modal-title">Pilar cadastrado</h2>
                  <p>O pilar foi vinculado ao produto e ja aparece na hierarquia administrativa.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}

        {isMetricModalOpen ? (
          <section className="admin-dialog-backdrop" role="presentation">
            <div className="admin-dialog" role="dialog" aria-modal="true" aria-labelledby="admin-metric-modal-title">
              {metricModalStep === "form" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Metrica</p>
                      <h2 id="admin-metric-modal-title">Cadastrar metrica</h2>
                    </div>
                    <button type="button" className="admin-inline-link" onClick={closeMetricCreateModal}>
                      Fechar
                    </button>
                  </div>
                  <form className="admin-client-form" onSubmit={handlePrepareMetricCreate}>
                    <label>
                      <span>Nome da metrica</span>
                      <input
                        name="name"
                        value={metricFormState.name}
                        onChange={(event) => setMetricFormState((current) => ({ ...current, name: event.target.value }))}
                        required
                      />
                    </label>
                    <label>
                      <span>Codigo</span>
                      <input
                        name="code"
                        value={metricFormState.code}
                        onChange={(event) => setMetricFormState((current) => ({ ...current, code: event.target.value }))}
                      />
                    </label>
                    <label>
                      <span>Direcao</span>
                      <select
                        name="direction"
                        value={metricFormState.direction}
                        onChange={(event) => setMetricFormState((current) => ({ ...current, direction: event.target.value as typeof current.direction }))}
                      >
                        <option value="higher_better">Maior melhor</option>
                        <option value="lower_better">Menor melhor</option>
                        <option value="target_range">Faixa alvo</option>
                      </select>
                    </label>
                    <label>
                      <span>Unidade</span>
                      <input
                        name="unit"
                        value={metricFormState.unit}
                        onChange={(event) => setMetricFormState((current) => ({ ...current, unit: event.target.value }))}
                      />
                    </label>
                    {metricFormError ? <p className="admin-form-error">{metricFormError}</p> : null}
                    <div className="admin-dialog__actions admin-client-form__full">
                      <button type="button" className="admin-inline-link" onClick={closeMetricCreateModal}>
                        Cancelar
                      </button>
                      <button type="submit" className="admin-inline-cta">
                        Continuar
                      </button>
                    </div>
                  </form>
                </>
              ) : null}

              {metricModalStep === "confirm" ? (
                <>
                  <div className="admin-dialog__header">
                    <div>
                      <p className="admin-module__eyebrow">Metrica</p>
                      <h2 id="admin-metric-modal-title">Confirmar cadastro da metrica</h2>
                    </div>
                  </div>
                  <div className="admin-dialog__summary">
                    <p>
                      <strong>{metricFormState.name}</strong>
                    </p>
                    {selectedPillar ? <p>{selectedPillar.name}</p> : null}
                    <p>{metricFormState.direction.replace("_", " ")}</p>
                    {metricFormState.unit ? <p>{metricFormState.unit}</p> : null}
                  </div>
                  {metricFormError ? <p className="admin-form-error">{metricFormError}</p> : null}
                  <div className="admin-dialog__actions">
                    <button type="button" className="admin-inline-link" onClick={() => setMetricModalStep("form")} disabled={metricSubmitting}>
                      Voltar
                    </button>
                    <button type="button" className="admin-inline-cta" onClick={() => void handleConfirmMetricCreate()} disabled={metricSubmitting}>
                      {metricSubmitting ? "Cadastrando..." : "Confirmar cadastro"}
                    </button>
                  </div>
                </>
              ) : null}

              {metricModalStep === "success" ? (
                <div className="admin-notice admin-notice--success">
                  <h2 id="admin-metric-modal-title">Metrica cadastrada</h2>
                  <p>A metrica foi vinculada ao pilar e ja aparece na estrutura administrativa.</p>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}
      </section>
    </AdminShell>
  );
}
