import { PhoneIcon } from '@heroicons/react/24/solid';
import { useNavigate } from 'react-router-dom';
import {useEffect, useState} from "react";


function ChoosePersona() {
  const navigate = useNavigate();

  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchPersonas = async () => {
      try {
        setLoading(true);
        const res = await fetch('http://localhost:7860/api/personas', { signal: controller.signal });

        if (!res.ok) throw new Error(`Error: ${res.statusText}`);

        const data = await res.json();

        setPersonas(data);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    };

    void fetchPersonas();

    return () => {
      controller.abort();
    };
  }, []);

  return (
          <div className="w-full text-center pt-8">
            <div className="mb-12">
              <h1 className="typography_h1">Choose a Practice Customer</h1>
              <p className="typography_body mt-4 max-w-3xl mx-auto">
                  Each one reflects a different personality or
                  challenge — from tough negotiators to friendly but indecisive callers — helping you build confidence in
                  real-world scenarios.
                </p>
            </div>
            {loading ? (
              <p className="typography_body text-gray-500">Loading personas...</p>
            ) : error ? (
              <p className="typography_body text-red-500">Failed to load: {error}</p>
            ) : (
              <div className="w-full flex justify-center">
                <div className="w-2/3 grid gap-8 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                  {personas.map((persona: any, idx) => (
                    <div
                      key={idx}
                      className="card flex flex-col items-center text-center h-[360px] w-full p-6 rounded-lg shadow"
                    >
                      <div className="w-32 h-32 mb-4">
                        <div
                          className="w-full h-full bg-center bg-no-repeat aspect-square bg-cover rounded-full"
                          style={{ backgroundImage: `url("${persona.img}")` }}
                        />

                      </div>
                      <h2 className="typography_h2 mb-2">{persona.title}</h2>
                      <p className="typography_body flex-grow">{persona.desc}</p>
                      <button
                        onClick={() => navigate('/call', { state: { persona } })}
                        className="button_primary mt-6 w-full flex items-center justify-center gap-2">
                        <PhoneIcon className="h-5 w-5 text-white" />
                        <span>Start Call</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
  );
}

export default ChoosePersona;
