export default function Toast({ toast, setToast }) {
  const [timer, setTimer] = useState(null);

  useEffect(() => {
    if (toast.show) {
      const newTimer = setTimeout(() => {
        setToast({ show: false, msg: "" });
      }, 3200);

      return () => clearTimeout(newTimer);
    }
  }, [toast.show]);

  return (
    <div
      className={`toast ${toast.show ? "show" : ""}`}
    >
      <Check size={14} color="#5FD888" strokeWidth={2.6} />

      {toast.msg}
    </div>
  );
}