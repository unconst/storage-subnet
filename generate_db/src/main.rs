extern crate rocksdb;
extern crate rand;
extern crate rand_chacha;
extern crate indicatif;
extern crate clap;
extern crate lazy_static;
use lazy_static::lazy_static;
use rayon::prelude::*;

use rocksdb::{DB, Options};
use indicatif::{MultiProgress, ProgressBar, ProgressStyle};
use clap::{App, Arg};
use sha2::{Sha256, Digest};
use rand::{Rng, SeedableRng, rngs::StdRng};

fn main() {
    let matches = App::new("RocksDB Chunk Generator")
    .arg(Arg::with_name("path")
        .long("path")
        .value_name("DB_PATH")
        .help("Path to the RocksDB database")
        .required(true)
        .takes_value(true))
    .arg(Arg::with_name("hash")
        .long("hash")
        .value_name("has")
        .help("Stores the hashes instead of the data itself.")
        .required(false)
        .takes_value(false))
    .arg(Arg::with_name("n")
        .long("n")
        .value_name("NUM_CHUNKS")
        .help("Number of chunks to generate")
        .required(true)
        .takes_value(true))
    .arg(Arg::with_name("size")
        .long("size")
        .value_name("CHUNK_SIZE")
        .help("Size of each chunk in bytes")
        .required(true)
        .takes_value(true))
    .arg(Arg::with_name("seed")
        .long("seed")
        .value_name("seed")
        .help("Seed used to generate the data.")
        .required(true)
        .takes_value(true))
    .get_matches();

    let hash = matches.is_present("hash");
    let path = matches.value_of("path").unwrap();
    let num_chunks: usize = matches.value_of("n").unwrap().parse().expect("Failed to parse number of chunks");
    let chunk_size: usize = matches.value_of("size").unwrap().parse().expect("Failed to parse chunk size");

    // Create a new RocksDB instance with default options
    let mut options = Options::default();
    options.create_if_missing(true);
    let db = DB::open(&options, path).expect("Failed to open database");

    // Seed-based PRNG
    let seed_data = matches.value_of("seed").unwrap();
    let seed_bytes = seed_data.as_bytes();
    let mut seed_array = [0u8; 32];
    if seed_bytes.len() > seed_array.len() {
        panic!("Seed length exceeds the maximum allowed length of 32 bytes.");
    }
    seed_array[..seed_bytes.len()].copy_from_slice(seed_bytes);
    
    // Set up the progress bar.
    let multi = MultiProgress::new();
    let pb = multi.add(ProgressBar::new(num_chunks as u64));
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})")
        .progress_chars("#>-"));

    // This spawns a new thread for the progress bars
    let _progress_thread_handle = std::thread::spawn(move || {
        multi.join().unwrap();
    });

    // Generate and store chunks
    (0..num_chunks).into_par_iter().for_each_with(pb, |pb, i| {
        let mut local_seed = seed_array;
        local_seed[0] = local_seed[0].wrapping_add(i as u8); // Modify the seed for diversification
        let mut prng = StdRng::from_seed(local_seed);
        let chunk_data = generate_string_chunk(&mut prng, chunk_size);
        // println!("Generated chunk data for key {}: {}", i, &chunk_data);
        let data_to_store = if hash {
            let mut hasher = Sha256::new();
            hasher.update(chunk_data.as_bytes());
            let computed_hash = format!("{:x}", hasher.finalize());
            // println!("Computed hash for key {}: {}", i, &computed_hash);
            computed_hash
        } else {
            chunk_data
        };
        // println!("Data being stored for key {}: {}", i, &data_to_store);

        db.put(i.to_string(), &data_to_store).expect("Failed to write to database");
        pb.inc(1);
    });

    // Wait for the progress bars to finish
    _progress_thread_handle.join().unwrap();
}

lazy_static! {
    static ref CHARS: Vec<char> = ('a'..='z').chain('A'..'Z').chain('0'..'9').collect();
}
fn generate_string_chunk(prng: &mut StdRng, size: usize) -> String {
    (0..size).map(|_| CHARS[prng.gen_range(0..CHARS.len())]).collect()
}
