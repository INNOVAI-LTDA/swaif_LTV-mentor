import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../../app/providers/AuthProvider";
import { useAdminClientDetail, useAdminClients } from "../../../domain/hooks/useAdminClients";
import { useAdminMetrics } from "../../../domain/hooks/useAdminMetrics";
import { useAdminMentors } from "../../../domain/hooks/useAdminMentors";
import { useAdminPillars } from "../../../domain/hooks/useAdminPillars";
import { useAdminProducts } from "../../../domain/hooks/useAdminProducts";
import { useAdminStudents } from "../../../domain/hooks/useAdminStudents";
import { createAdminClient } from "../../../domain/services/adminClientService";
import { createAdminMetric, listAdminMetricsByProduct } from "../../../domain/services/adminMetricService";
import { createAdminMentor } from "../../../domain/services/adminMentorService";
import { createAdminPillar } from "../../../domain/services/adminPillarService";
import { createAdminProduct } from "../../../domain/services/adminProductService";
import { createAdminStudent, loadAdminStudentIndicators, reassignAdminStudent, unlinkAdminStudent } from "../../../domain/services/adminStudentService";
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

const CREATE_OPTIONS: Array<{ key: CreateTarget; label: string }> = [
  { key: "cliente", label: "Cliente" },
  { key: "produto", label: "Produto" },
  { key: "mentor", label: "Mentor" },
  { key: "pilar", label: "Pilar" },
  { key: "metrica", label: "Metrica" },
  { key: "aluno", label: "Aluno" }
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

  const activePanel = searchParams.get("panel");
  const isClientsPanel = activePanel === "clientes";
  const isProductsPanel = activePanel === "produtos";
  const isMentorsPanel = activePanel === "mentores";
  const isStudentsPanel = activePanel === "alunos";
  const hasContextPanel = isClientsPanel || isProductsPanel || isMentorsPanel || isStudentsPanel;
  const hasProductContextPanel = isProductsPanel || isMentorsPanel || isStudentsPanel;
  const showClientSectionBar = !hasContextPanel;

  const clientDetailResource = useAdminClientDetail(canLoadAdmin ? selectedClientId : null, canLoadAdmin);
  const productsResource = useAdminProducts(canLoadAdmin && hasContextPanel ? selectedClientId : null);
  const mentorsResource = useAdminMentors(canLoadAdmin && hasProductContextPanel ? selectedProductId : null);
  const pillarsResource = useAdminPillars(canLoadAdmin && hasProductContextPanel ? selectedProductId : null);
  const metricsResource = useAdminMetrics(canLoadAdmin && isProductsPanel ? selectedPillarId : null);
  const studentsResource = useAdminStudents(canLoadAdmin && isStudentsPanel ? selectedMentorId : null);

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
    if (!isStudentsPanel || studentsResource.data.length === 0) {
      if (selectedStudentId !== null) {
        setSelectedStudentId(null);
      }
      return;
    }
    if (!studentsResource.data.some((item) => item.id === selectedStudentId)) {
      setSelectedStudentId(studentsResource.data[0].id);
    }
  }, [isStudentsPanel, selectedStudentId, studentsResource.data]);

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

  return (
    <AdminShell
      eyebrow="Admin | Operacao administrativa real"
      title="Centro Institucional"
      description="Bloco 8 da Fase 2 operando Cliente/Empresa, Produto/Mentoria, Mentor, Aluno, Pilar, Metrica e carga inicial de indicadores com contexto real por aluno."
      metrics={[
        { label: "Clientes ativos", value: String(activeClients.length), tone: "accent" },
        { label: "Produtos do cliente", value: hasContextPanel ? String(productsResource.data.length) : "-", tone: "warning" },
        { label: "Mentores do produto", value: hasProductContextPanel ? String(mentorsResource.data.length) : "-", tone: "warning" },
        { label: "Pilares do produto", value: hasProductContextPanel ? String(pillarsResource.data.length) : "-", tone: "warning" },
        { label: "Metricas do pilar", value: isProductsPanel ? String(metricsResource.data.length) : "-", tone: "warning" },
        { label: "Bloco em foco", value: isStudentsPanel ? "Ingestao" : "Metrica", tone: "success" }
      ]}
    >
      <section className="admin-page">
        {!isAuthenticated || user?.role !== "admin" ? (
          <section className="admin-notice">
            <strong>Entre com o usuario admin para operar o bloco real.</strong>
            <p>Use credenciais administrativas validas para este ambiente. Sem essa sessao, a API administrativa respondera com erro de autorizacao.</p>
          </section>
        ) : null}

        <section className="admin-module admin-clients-stage">
          {showClientSectionBar ? (
            <div className="admin-section-bar">
              <div>
                <p className="admin-module__eyebrow">Cliente/Empresa</p>
                <h2>Clientes ativos</h2>
              </div>
              <div className="admin-section-bar__actions">
                <button type="button" className="admin-inline-cta" onClick={openClientCreateModal}>
                  Cadastrar cliente
                </button>
              </div>
            </div>
          ) : null}

          {clientsResource.loading && clientsResource.data.length === 0 ? <p className="admin-state">Carregando clientes...</p> : null}
          {clientsResource.error && clientsResource.data.length === 0 ? (
            <div className="admin-state admin-state--error">
              <p>{clientsResource.error}</p>
              <button type="button" onClick={() => void clientsResource.refresh()}>
                Tentar novamente
              </button>
            </div>
          ) : null}
          {!clientsResource.loading && !clientsResource.error && activeClients.length === 0 ? (
            <p className="admin-state">Nenhum cliente ativo cadastrado ainda. Use o botao de cadastro para iniciar a operacao.</p>
          ) : null}

          {!hasContextPanel && activeClients.length > 0 ? (
            <ul className="admin-client-grid" aria-label="Clientes ativos">
              {activeClients.map((client) => (
                <li key={client.id}>
                  <button type="button" className="admin-client-card" onClick={() => openClientArea(client.id)}>
                    <span>{formatCnpj(client.cnpj)}</span>
                    <strong>{client.name}</strong>
                    <small>{client.brand_name || "Cliente institucional"}</small>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}

          {isClientsPanel && selectedClient ? (
            <div className="admin-client-panel">
              {renderCreateChooser()}
              <div className="admin-client-focus">
                <article className="admin-client-card admin-client-card--spotlight">
                  <span>{formatCnpj(selectedClient.cnpj)}</span>
                  <strong>{selectedClient.name}</strong>
                  <small>{selectedClient.brand_name || "Cliente institucional"}</small>
                </article>

                <section className="admin-product-stage">
                  {productsResource.loading && productsResource.data.length === 0 ? <p className="admin-state">Carregando produtos...</p> : null}
                  {productsResource.error && productsResource.data.length === 0 ? (
                    <div className="admin-state admin-state--error">
                      <p>{productsResource.error}</p>
                      <button type="button" onClick={() => void productsResource.refresh()}>
                        Tentar novamente
                      </button>
                    </div>
                  ) : null}
                  {!productsResource.loading && !productsResource.error && productsResource.data.length === 0 ? (
                    <div className="admin-empty-stack">
                      <p className="admin-state">Nenhum produto cadastrado para este cliente.</p>
                    </div>
                  ) : null}
                  {productsResource.data.length > 0 ? (
                    <ul className="admin-product-grid" aria-label="Produtos do cliente">
                      {productsResource.data.map((product) => (
                        <li key={product.id}>
                          <button
                            type="button"
                            className={product.id === selectedProductId ? "admin-product-card is-active" : "admin-product-card"}
                            onClick={() => openProductArea(product.id)}
                          >
                            <span>{product.code}</span>
                            <strong>{product.name}</strong>
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              </div>
            </div>
          ) : null}

          {isProductsPanel ? (
            <div className="admin-product-panel">
              {renderCreateChooser()}
              {productsResource.loading && productsResource.data.length === 0 ? <p className="admin-state">Carregando produtos...</p> : null}
              {productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-state admin-state--error">
                  <p>{productsResource.error}</p>
                  <button type="button" onClick={() => void productsResource.refresh()}>
                    Tentar novamente
                  </button>
                </div>
              ) : null}
              {!productsResource.loading && !productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-empty-stack">
                  <p className="admin-state">Nenhum produto cadastrado para este cliente.</p>
                </div>
              ) : null}

              {selectedProduct ? (
                <div className="admin-product-hierarchy">
                  <button
                    type="button"
                    className="admin-hierarchy-card admin-hierarchy-card--product"
                    onClick={() => {
                      setIsPillarExpanded(false);
                      setSelectedPillarId(null);
                    }}
                  >
                    <span>{selectedProduct.code}</span>
                    <strong>{selectedProduct.name}</strong>
                    <small>{selectedProduct.delivery_model}</small>
                  </button>
                  {selectedMentor ? (
                    <button type="button" className="admin-hierarchy-card admin-hierarchy-card--action" onClick={() => openMentorArea(selectedProduct.id)}>
                      <span>Mentor</span>
                      <strong>{selectedMentor.full_name}</strong>
                      <small>{selectedMentor.email}</small>
                    </button>
                  ) : (
                    <article className="admin-hierarchy-card">
                      <span>Mentor</span>
                      <strong>Nenhum Mentor Cadastrado</strong>
                      <small>Use Cadastrar... para vincular o mentor principal.</small>
                    </article>
                  )}
                  <div className="admin-pillar-stack">
                    {!isPillarExpanded ? (
                      <button
                        type="button"
                        className={pillarCards.length > 0 ? "admin-hierarchy-card admin-hierarchy-card--action" : "admin-hierarchy-card"}
                        onClick={togglePillarStack}
                        disabled={pillarCards.length === 0}
                      >
                        <span>Pilar</span>
                        <strong>
                          {pillarsResource.loading && pillarCards.length === 0
                            ? "Carregando pilares..."
                            : pillarCards.length > 0
                              ? "Clique para abrir"
                              : "Nenhum Pilar Cadastrado"}
                        </strong>
                        <small>
                          {pillarsResource.error && pillarCards.length === 0
                            ? pillarsResource.error
                            : pillarCards.length > 0
                              ? `${pillarCards.length} pilares vinculados`
                              : "Use Cadastrar... para estruturar o produto."}
                        </small>
                      </button>
                    ) : null}
                    <div className={isPillarExpanded ? "admin-pillar-list is-open" : "admin-pillar-list"}>
                      {pillarCards.map((pillar) => {
                        const isMetricOpen = selectedPillarId === pillar.id;
                        return (
                          <div key={pillar.id} className="admin-pillar-entry">
                            <button
                              type="button"
                              className={isMetricOpen ? "admin-hierarchy-card admin-hierarchy-card--pillar is-selected" : "admin-hierarchy-card admin-hierarchy-card--pillar"}
                              onClick={() => toggleMetricStack(pillar.id)}
                            >
                              <span>{pillar.label}</span>
                              <strong>{pillar.title}</strong>
                              <small>{pillar.detail}</small>
                            </button>
                            {isMetricOpen ? (
                              <div className="admin-metric-stack">
                                {metricsResource.loading && metricsResource.data.length === 0 ? <p className="admin-state">Carregando metricas...</p> : null}
                                {metricsResource.error && metricsResource.data.length === 0 ? (
                                  <div className="admin-state admin-state--error">
                                    <p>{metricsResource.error}</p>
                                    <button type="button" onClick={() => void metricsResource.refresh()}>
                                      Tentar novamente
                                    </button>
                                  </div>
                                ) : null}
                                {!metricsResource.loading && !metricsResource.error && metricsResource.data.length === 0 ? (
                                  <div className="admin-empty-stack">
                                    <p className="admin-state">Nenhuma metrica cadastrada para {pillar.title}.</p>
                                  </div>
                                ) : null}
                                {metricsResource.data.length > 0 ? (
                                  <ul className="admin-metric-list" aria-label={`Metricas do pilar ${pillar.title}`}>
                                    {metricsResource.data.map((metric) => (
                                      <li key={metric.id}>
                                        <article className="admin-metric-card">
                                          <span>{metric.direction.replace("_", " ")}</span>
                                          <strong>{metric.name}</strong>
                                          <small>{metric.unit || metric.code.toUpperCase()}</small>
                                        </article>
                                      </li>
                                    ))}
                                  </ul>
                                ) : null}
                              </div>
                            ) : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {isMentorsPanel ? (
            <div className="admin-product-panel">
              {renderCreateChooser()}
              {productsResource.loading && productsResource.data.length === 0 ? <p className="admin-state">Carregando produtos...</p> : null}
              {productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-state admin-state--error">
                  <p>{productsResource.error}</p>
                  <button type="button" onClick={() => void productsResource.refresh()}>
                    Tentar novamente
                  </button>
                </div>
              ) : null}
              {!productsResource.loading && !productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-empty-stack">
                  <p className="admin-state">Nenhum produto cadastrado para este cliente.</p>
                </div>
              ) : null}

              {selectedProduct ? (
                <div className="admin-mentor-focus">
                  <article className="admin-hierarchy-card admin-hierarchy-card--product">
                    <span>{selectedProduct.code}</span>
                    <strong>{selectedProduct.name}</strong>
                    <small>{selectedProduct.delivery_model}</small>
                  </article>
                  <section className="admin-mentor-stage">
                    {mentorsResource.loading && mentorsResource.data.length === 0 ? <p className="admin-state">Carregando mentores...</p> : null}
                    {mentorsResource.error && mentorsResource.data.length === 0 ? (
                      <div className="admin-state admin-state--error">
                        <p>{mentorsResource.error}</p>
                        <button type="button" onClick={() => void mentorsResource.refresh()}>
                          Tentar novamente
                        </button>
                      </div>
                    ) : null}
                    {!mentorsResource.loading && !mentorsResource.error && mentorsResource.data.length === 0 ? (
                      <div className="admin-empty-stack">
                        <p className="admin-state">Nenhum mentor cadastrado para este produto.</p>
                      </div>
                    ) : null}
                    {mentorsResource.data.length > 0 ? (
                      <ul className="admin-mentor-grid" aria-label="Mentores do produto">
                        {mentorsResource.data.map((mentor) => (
                          <li key={mentor.id}>
                            <button
                              type="button"
                              className={mentor.id === selectedMentor?.id ? "admin-mentor-card is-primary" : "admin-mentor-card"}
                              onClick={() => openStudentArea(mentor.id)}
                            >
                              <span>{mentor.id === selectedProduct.mentor_id ? "Mentor principal" : "Mentor"}</span>
                              <strong>{mentor.full_name}</strong>
                              <small>{mentor.email}</small>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </section>
                </div>
              ) : null}
            </div>
          ) : null}

          {isStudentsPanel ? (
            <div className="admin-product-panel">
              {renderStudentPanelActions()}
              {productsResource.loading && productsResource.data.length === 0 ? <p className="admin-state">Carregando produtos...</p> : null}
              {productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-state admin-state--error">
                  <p>{productsResource.error}</p>
                  <button type="button" onClick={() => void productsResource.refresh()}>
                    Tentar novamente
                  </button>
                </div>
              ) : null}
              {!productsResource.loading && !productsResource.error && productsResource.data.length === 0 ? (
                <div className="admin-empty-stack">
                  <p className="admin-state">Nenhum produto cadastrado para este cliente.</p>
                </div>
              ) : null}

              {selectedProduct && selectedMentor ? (
                <div className="admin-student-focus">
                  <article className="admin-hierarchy-card admin-hierarchy-card--product">
                    <span>{selectedProduct.code}</span>
                    <strong>{selectedProduct.name}</strong>
                    <small>{selectedProduct.delivery_model}</small>
                  </article>
                  <article className="admin-hierarchy-card">
                    <span>Mentor</span>
                    <strong>{selectedMentor.full_name}</strong>
                    <small>{selectedMentor.email}</small>
                  </article>
                  <section className="admin-student-stage">
                    {studentsResource.loading && studentsResource.data.length === 0 ? <p className="admin-state">Carregando alunos...</p> : null}
                    {studentsResource.error && studentsResource.data.length === 0 ? (
                      <div className="admin-state admin-state--error">
                        <p>{studentsResource.error}</p>
                        <button type="button" onClick={() => void studentsResource.refresh()}>
                          Tentar novamente
                        </button>
                      </div>
                    ) : null}
                    {!studentsResource.loading && !studentsResource.error && studentsResource.data.length === 0 ? (
                      <div className="admin-empty-stack">
                        <p className="admin-state">Nenhum aluno cadastrado para este mentor.</p>
                      </div>
                    ) : null}
                    {studentsResource.data.length > 0 ? (
                      <ul className="admin-student-grid" aria-label="Alunos do mentor">
                        {studentsResource.data.map((student) => (
                          <li key={student.id}>
                            <button
                              type="button"
                              className={student.id === selectedStudent?.id ? "admin-student-card is-selected" : "admin-student-card"}
                              onClick={() => setSelectedStudentId(student.id)}
                            >
                              <span>{student.initials}</span>
                              <strong>{student.full_name}</strong>
                              <small>{student.email || formatCpf(student.cpf || "")}</small>
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </section>
                </div>
              ) : null}
            </div>
          ) : null}
        </section>

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
